<#
.SYNOPSIS
Windows local Ollama setup, tests, and CLI verification.
.EXAMPLE
.\scripts\windows-local.ps1 -Action All
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Setup', 'Test', 'Verify', 'All')]
    [string]$Action,
    [ValidateNotNullOrEmpty()]
    [string]$Model = 'tinyllama:latest',
    [ValidateScript({ $_ -gt 0 -and -not [double]::IsInfinity($_) -and -not [double]::IsNaN($_) })]
    [double]$Timeout = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:RepoRoot = Split-Path -Parent $PSScriptRoot
$script:BaseUrl = 'http://127.0.0.1:11434'
$script:ReadyWaitSeconds = 60

function Invoke-External {
    param([string]$FilePath, [string[]]$Arguments)
    # Windows PowerShell 5.1 can turn native stderr into error records.
    # A native command's exit code, rather than its stderr, determines success.
    $ErrorActionPreference = 'Continue'
    $PSNativeCommandUseErrorActionPreference = $false
    $global:LASTEXITCODE = $null
    & $FilePath @Arguments | Out-Host
    $code = $global:LASTEXITCODE
    if ($null -eq $code) { throw "No exit code from $FilePath." }
    return [int]$code
}

function Find-Python {
    $candidates = @()
    $launcher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($launcher) {
        $candidates += [pscustomobject]@{ Path = $launcher.Source; Prefix = @('-3') }
    }
    $native = Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($native) {
        $candidates += [pscustomobject]@{ Path = $native.Source; Prefix = @() }
    }
    foreach ($registryRoot in @('HKCU:\Software\Python\PythonCore', 'HKLM:\Software\Python\PythonCore')) {
        if (Test-Path -LiteralPath $registryRoot) {
            foreach ($version in Get-ChildItem -LiteralPath $registryRoot) {
                $installKey = Join-Path $version.PSPath 'InstallPath'
                if (Test-Path -LiteralPath $installKey) {
                    $directory = (Get-Item -LiteralPath $installKey).GetValue('')
                    if ($directory) {
                        $candidates += [pscustomobject]@{
                            Path = (Join-Path $directory 'python.exe'); Prefix = @()
                        }
                    }
                }
            }
        }
    }
    $userPython = Join-Path $env:LOCALAPPDATA 'Programs\Python'
    if (Test-Path -LiteralPath $userPython) {
        foreach ($directory in Get-ChildItem -LiteralPath $userPython -Directory -Filter 'Python3*') {
            $candidates += [pscustomobject]@{
                Path = (Join-Path $directory.FullName 'python.exe'); Prefix = @()
            }
        }
    }
    foreach ($candidate in $candidates) {
        if ($candidate.Path -match '[\\/](WindowsApps|\.venv)[\\/]' -or
            -not (Test-Path -LiteralPath $candidate.Path -PathType Leaf)) { continue }
        $probe = @($candidate.Prefix) + @(
            '-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'
        )
        $ErrorActionPreference = 'Continue'
        $PSNativeCommandUseErrorActionPreference = $false
        try {
            $global:LASTEXITCODE = $null
            & $candidate.Path @probe 2>$null | Out-Null
            $code = $global:LASTEXITCODE
        } catch {
            throw "Python could not execute. Check application-control policy: $($_.Exception.Message)"
        }
        if ($null -eq $code) { throw 'Python did not execute. Check application-control policy.' }
        if ($code -eq 0) { return $candidate }
    }
    return $null
}

function Find-Ollama {
    $command = Get-Command ollama.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $installed = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (Test-Path -LiteralPath $installed -PathType Leaf) { return $installed }
    return $null
}

function Install-Package {
    param([string]$PackageId)
    $winget = Get-Command winget.exe -CommandType Application -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw 'winget is missing. Install/update App Installer, or install the prerequisite manually.'
    }
    Write-Host "Installing missing prerequisite: $PackageId"
    $code = Invoke-External $winget.Source @(
        'install', '--id', $PackageId, '--exact', '--source', 'winget',
        '--no-upgrade', '--silent', '--accept-source-agreements',
        '--accept-package-agreements', '--disable-interactivity'
    )
    if ($code -ne 0) { throw "winget installation failed for $PackageId (exit $code)." }
}

function Get-LocalModels {
    param([int]$TimeoutMilliseconds = 3000)
    $request = [System.Net.HttpWebRequest]::Create("$script:BaseUrl/api/tags")
    $request.Proxy = $null
    $request.Timeout = $TimeoutMilliseconds
    $request.ReadWriteTimeout = $TimeoutMilliseconds
    $response = $null
    $reader = $null
    try {
        $response = $request.GetResponse()
        if ([int]$response.StatusCode -ne 200) { throw '/api/tags did not return HTTP 200.' }
        $reader = [System.IO.StreamReader]::new($response.GetResponseStream())
        $tags = $reader.ReadToEnd() | ConvertFrom-Json
        if ($null -eq $tags -or $null -eq $tags.PSObject.Properties['models'] -or
            $tags.models -isnot [array]) {
            throw '/api/tags did not return an Ollama model list.'
        }
        return $tags
    } finally {
        if ($reader) { $reader.Dispose() }
        if ($response) { $response.Dispose() }
    }
}

function Start-OllamaApp {
    param([string]$OllamaPath)
    $app = Join-Path (Split-Path -Parent $OllamaPath) 'ollama app.exe'
    if (-not (Test-Path -LiteralPath $app -PathType Leaf)) {
        throw 'Ollama app not found beside ollama.exe. Start Ollama manually and rerun Setup.'
    }
    Start-Process -FilePath $app -WindowStyle Hidden | Out-Null
}

function Wait-OllamaReady {
    param([string]$OllamaPath)
    try { return Get-LocalModels } catch { Write-Host 'Starting Ollama; waiting up to 60 seconds.' }
    Start-OllamaApp $OllamaPath
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $lastFailure = ''
    while ($timer.Elapsed.TotalSeconds -lt $script:ReadyWaitSeconds) {
        $remaining = [int](($script:ReadyWaitSeconds - $timer.Elapsed.TotalSeconds) * 1000)
        if ($remaining -le 0) { break }
        try {
            return Get-LocalModels -TimeoutMilliseconds ([Math]::Min(3000, $remaining))
        } catch { $lastFailure = $_.Exception.Message }
        $remaining = [int](($script:ReadyWaitSeconds - $timer.Elapsed.TotalSeconds) * 1000)
        if ($remaining -le 0) { break }
        Start-Sleep -Milliseconds ([Math]::Min(1000, $remaining))
    }
    throw "Ollama did not become ready at $script:BaseUrl. $lastFailure"
}

function Invoke-OllamaPull {
    param([string]$OllamaPath, [string]$ModelName)
    # Quote a Windows argv element, including embedded quotes and trailing slashes.
    $escaped = [regex]::Replace($ModelName, '(\\*)"', '$1$1\"')
    $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
    $info = [System.Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $OllamaPath
    $info.Arguments = 'pull "' + $escaped + '"'
    $info.UseShellExecute = $false
    # Only this child targets loopback. No user, machine, or parent variable changes.
    $info.EnvironmentVariables['OLLAMA_HOST'] = $script:BaseUrl
    $process = [System.Diagnostics.Process]::Start($info)
    try {
        $process.WaitForExit()
        return $process.ExitCode
    } finally { $process.Dispose() }
}

function Invoke-Setup {
    $python = Find-Python
    if (-not $python) {
        Install-Package 'Python.Python.3.12'
        $python = Find-Python
        if (-not $python) { throw 'Python 3.12+ is still unavailable after installation.' }
    }
    $ollama = Find-Ollama
    if (-not $ollama) {
        Install-Package 'Ollama.Ollama'
        $ollama = Find-Ollama
        if (-not $ollama) { throw 'Ollama is still unavailable after installation.' }
    }
    $tags = Wait-OllamaReady $ollama
    $names = @($tags.models | ForEach-Object { $_.name })
    $expectedModel = $Model
    if ($Model -notmatch ':' -and $Model -notmatch '@') { $expectedModel += ':latest' }
    if ($names -contains $expectedModel) {
        Write-Host "Model already available: $expectedModel"
    } else {
        Write-Host "Downloading model: $Model (this may take several minutes)."
        $code = Invoke-OllamaPull $ollama $Model
        if ($code -ne 0) { throw "Model download failed (exit $code)." }
        $tags = Get-LocalModels
        if (@($tags.models | ForEach-Object { $_.name }) -notcontains $expectedModel) {
            throw "Model not present after pull: $expectedModel"
        }
    }
    Write-Host 'SETUP_OK'
}

function Require-Python {
    $python = Find-Python
    if (-not $python) { throw 'Python 3.12+ is missing. Run -Action Setup first.' }
    return $python
}

function Invoke-Tests {
    $python = Require-Python
    foreach ($arguments in @(
        @('-m', 'unittest', 'discover', '-s', 'tests', '-v'),
        @('client.py', '--help'),
        @('-m', 'compileall', '-q', 'client.py', 'tests')
    )) {
        $code = Invoke-External $python.Path (@($python.Prefix) + $arguments)
        if ($code -ne 0) { throw "Python check failed (exit $code): $($arguments -join ' ')" }
    }
    Write-Host 'TEST_OK'
}

function Invoke-Verification {
    $python = Require-Python
    $code = Invoke-External $python.Path (@($python.Prefix) + @(
        'client.py', '--base-url', $script:BaseUrl, '--model', $Model,
        '--timeout', $Timeout.ToString([System.Globalization.CultureInfo]::InvariantCulture)
    ))
    if ($code -notin @(0, 2, 3)) { throw "Python CLI failed to execute normally (exit $code)." }
    return $code
}

function Invoke-Workflow {
    param([string]$SelectedAction)
    if ($SelectedAction -in @('Setup', 'All')) { Invoke-Setup }
    if ($SelectedAction -in @('Test', 'All')) { Invoke-Tests }
    if ($SelectedAction -in @('Verify', 'All')) { return Invoke-Verification }
    return 0
}

if ($env:OS -ne 'Windows_NT') {
    [Console]::Error.WriteLine('This script requires Windows.')
    exit 1
}
$exitCode = 1
Push-Location -LiteralPath $script:RepoRoot
try {
    $exitCode = Invoke-Workflow $Action
} catch {
    [Console]::Error.WriteLine("FAILED: $($_.Exception.Message)")
    $exitCode = 1
} finally {
    Pop-Location
}
exit $exitCode
