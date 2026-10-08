# Standalone PowerShell tests. No Python, installer, model pull, or app is executed.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts\windows-local.ps1'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    $scriptPath, [ref]$tokens, [ref]$parseErrors
)
if ($parseErrors.Count) { throw ($parseErrors.Message -join '; ') }
$definitions = $ast.EndBlock.Statements |
    Where-Object { $_ -is [System.Management.Automation.Language.FunctionDefinitionAst] }
. ([scriptblock]::Create(($definitions.Extent.Text -join [Environment]::NewLine)))
$Model = 'tinyllama:latest'
$Timeout = [double]180
$script:BaseUrl = 'http://127.0.0.1:11434'
$script:ReadyWaitSeconds = 0
$script:Passed = 0

function Assert-Equal {
    param($Actual, $Expected)
    if ($Actual -ne $Expected) { throw "Expected [$Expected], got [$Actual]." }
}
function Assert-Throws {
    param([scriptblock]$Body, [string]$Message)
    $failure = $null
    try { & $Body | Out-Null } catch { $failure = $_.Exception.Message }
    if (-not $failure -or $failure -notlike "*$Message*") {
        throw "Expected error containing [$Message], got [$failure]."
    }
}
function Test-Case {
    param([string]$Name, [scriptblock]$Body)
    & $Body
    $script:Passed++
    Write-Host "PASS: $Name"
}
function Fake-Python {
    return [pscustomobject]@{ Path = 'unused-python.exe'; Prefix = @('-3') }
}
function Existing-Tags {
    return [pscustomobject]@{ models = @([pscustomobject]@{ name = 'tinyllama:latest' }) }
}

Test-Case 'Existing Setup skips installers and model download on repeated runs' {
    function Find-Python { Fake-Python }
    function Find-Ollama { 'unused-ollama.exe' }
    function Wait-OllamaReady { Existing-Tags }
    function Install-Package { throw 'Unexpected installation' }
    function Invoke-OllamaPull { throw 'Unexpected model download' }
    Invoke-Setup
    Invoke-Setup
}
Test-Case 'Setup re-resolves Python after installing a missing prerequisite' {
    $script:PythonCalls = 0
    $script:Installed = @()
    function Find-Python {
        $script:PythonCalls++
        if ($script:PythonCalls -gt 1) { Fake-Python }
    }
    function Find-Ollama { 'unused-ollama.exe' }
    function Install-Package { param($PackageId); $script:Installed += $PackageId }
    function Wait-OllamaReady { Existing-Tags }
    Invoke-Setup
    Assert-Equal $script:PythonCalls 2
    Assert-Equal ($script:Installed -join ',') 'Python.Python.3.12'
}
Test-Case 'Setup re-resolves Ollama after installation' {
    $script:OllamaCalls = 0
    $script:Installed = @()
    function Find-Python { Fake-Python }
    function Find-Ollama {
        $script:OllamaCalls++
        if ($script:OllamaCalls -gt 1) { 'unused-ollama.exe' }
    }
    function Install-Package { param($PackageId); $script:Installed += $PackageId }
    function Wait-OllamaReady { Existing-Tags }
    Invoke-Setup
    Assert-Equal $script:OllamaCalls 2
    Assert-Equal ($script:Installed -join ',') 'Ollama.Ollama'
}
Test-Case 'Missing winget is actionable' {
    function Get-Command { param($Name, $CommandType, $ErrorAction); return $null }
    Assert-Throws { Install-Package 'Ollama.Ollama' } 'winget is missing'
}
Test-Case 'Installer failure stops Setup before subsequent work' {
    function Get-Command {
        param($Name, $CommandType, $ErrorAction)
        [pscustomobject]@{ Source = 'unused-winget.exe' }
    }
    function Invoke-External { return 17 }
    Assert-Throws { Install-Package 'Ollama.Ollama' } 'exit 17'
}
Test-Case 'Existing healthy service does not start another app' {
    function Get-LocalModels { Existing-Tags }
    function Start-OllamaApp { throw 'Unexpected app start' }
    $tags = Wait-OllamaReady 'unused-ollama.exe'
    Assert-Equal $tags.models[0].name 'tinyllama:latest'
}
Test-Case 'Unready service reports failure rather than proceeding to download' {
    function Get-LocalModels { throw 'Connection refused' }
    function Start-OllamaApp {}
    Assert-Throws { Wait-OllamaReady 'unused-ollama.exe' } 'did not become ready'
}
Test-Case 'Failed model pull is not treated as success' {
    function Find-Python { Fake-Python }
    function Find-Ollama { 'unused-ollama.exe' }
    function Wait-OllamaReady { [pscustomobject]@{ models = @() } }
    function Invoke-OllamaPull { return 9 }
    function Get-LocalModels { throw 'Unexpected recheck' }
    Assert-Throws { Invoke-Setup } 'Model download failed'
}
Test-Case 'Successful pull requires the model to appear in tags' {
    function Find-Python { Fake-Python }
    function Find-Ollama { 'unused-ollama.exe' }
    function Wait-OllamaReady { [pscustomobject]@{ models = @() } }
    function Invoke-OllamaPull { return 0 }
    function Get-LocalModels { [pscustomobject]@{ models = @() } }
    Assert-Throws { Invoke-Setup } 'Model not present'
}
Test-Case 'First Python test failure prevents later commands' {
    $script:ExternalCalls = 0
    function Require-Python { Fake-Python }
    function Invoke-External { $script:ExternalCalls++; return 8 }
    Assert-Throws { Invoke-Tests } 'Python check failed'
    Assert-Equal $script:ExternalCalls 1
}
Test-Case 'All runs Setup, Test, Verify in order and propagates CLI error' {
    $script:Stages = @()
    function Invoke-Setup { $script:Stages += 'Setup' }
    function Invoke-Tests { $script:Stages += 'Test' }
    function Invoke-Verification { $script:Stages += 'Verify'; return 2 }
    Assert-Equal (Invoke-Workflow 'All') 2
    Assert-Equal ($script:Stages -join ',') 'Setup,Test,Verify'
}
Test-Case 'All stops immediately at a failing Setup' {
    function Invoke-Setup { throw 'Setup failed' }
    function Invoke-Tests { throw 'Should never test' }
    function Invoke-Verification { throw 'Should never verify' }
    Assert-Throws { Invoke-Workflow 'All' } 'Setup failed'
}
Test-Case 'All stops at a failing Test' {
    function Invoke-Setup {}
    function Invoke-Tests { throw 'Test failed' }
    function Invoke-Verification { throw 'Should never verify' }
    Assert-Throws { Invoke-Workflow 'All' } 'Test failed'
}
Test-Case 'Verify preserves generated, API error, and transport/invalid exit codes' {
    function Require-Python { Fake-Python }
    function Invoke-External { return $script:NativeResult }
    foreach ($code in @(0, 2, 3)) {
        $script:NativeResult = $code
        Assert-Equal (Invoke-Verification) $code
    }
}
Test-Case 'Unexpected CLI execution failure becomes a script error' {
    function Require-Python { Fake-Python }
    function Invoke-External { return 7 }
    Assert-Throws { Invoke-Verification } 'failed to execute normally'
}
Test-Case 'Verify uses fixed loopback and culture-independent timeout' {
    function Require-Python { Fake-Python }
    function Invoke-External {
        param($FilePath, $Arguments)
        Assert-Equal $Arguments[0] '-3'
        Assert-Equal $Arguments[3] 'http://127.0.0.1:11434'
        Assert-Equal $Arguments[-1] '180'
        return 0
    }
    Assert-Equal (Invoke-Verification) 0
}
Test-Case 'External process exit code is retained' {
    Assert-Equal (Invoke-External $env:ComSpec @('/d', '/c', 'exit 7')) 7
}
Test-Case 'Native stderr alone does not fail a successful process' {
    $shell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
    Assert-Equal (Invoke-External $shell @(
        '-NoProfile', '-Command', "[Console]::Error.WriteLine('expected stderr'); exit 0"
    )) 0
}
Test-Case 'Failed process launch cannot reuse a previous successful exit code' {
    $global:LASTEXITCODE = 0
    Assert-Throws {
        Invoke-External (Join-Path $env:TEMP 'nonexistent-codex-ollama-test.exe') @()
    } 'nonexistent-codex-ollama-test.exe'
}

Test-Case 'Main entry works from another directory and a repo path containing spaces' {
    $fixtureRoot = Join-Path $env:TEMP ('Ollama local test ' + [guid]::NewGuid().ToString('N'))
    $fixtureScripts = Join-Path $fixtureRoot 'scripts'
    $fixtureScript = Join-Path $fixtureScripts 'windows-local.ps1'
    $shell = Join-Path $PSHOME 'powershell.exe'
    if ($PSVersionTable.PSVersion.Major -ge 6) { $shell = Join-Path $PSHOME 'pwsh.exe' }
    New-Item -ItemType Directory -Path $fixtureScripts -Force | Out-Null
    [IO.File]::WriteAllText((Join-Path $fixtureRoot 'client.py'), '# Path fixture only; never executed.')
    try {
        foreach ($expectedCode in @(0, 2, 3)) {
            $fixtureText = [IO.File]::ReadAllText($scriptPath)
            $replacements = @($ast.EndBlock.Statements | Where-Object {
                $_ -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
                $_.Name -in @('Find-Python', 'Invoke-External')
            } | Sort-Object { $_.Extent.StartOffset } -Descending)
            foreach ($node in $replacements) {
                if ($node.Name -eq 'Find-Python') {
                    $body = 'function Find-Python { return [pscustomobject]@{Path="fixture";Prefix=@()} }'
                } else {
                    $body = @'
function Invoke-External {
    param($FilePath, $Arguments)
    if ((Get-Location).Path -ne $script:RepoRoot -or -not (Test-Path -LiteralPath 'client.py')) {
        throw 'Script did not enter the fixture repo.'
    }
    if ($Arguments -contains '--base-url') { return __CODE__ }
    return 0
}
'@
                    $body = $body.Replace('__CODE__', [string]$expectedCode)
                }
                $fixtureText = $fixtureText.Remove(
                    $node.Extent.StartOffset, $node.Extent.EndOffset - $node.Extent.StartOffset
                ).Insert($node.Extent.StartOffset, $body)
            }
            [IO.File]::WriteAllText($fixtureScript, $fixtureText, [Text.UTF8Encoding]::new($true))
            Push-Location -LiteralPath $env:TEMP
            try {
                $actualCode = Invoke-External $shell @(
                    '-NoProfile', '-File', $fixtureScript, '-Action', 'Verify'
                )
                Assert-Equal $actualCode $expectedCode
                Assert-Equal (Invoke-External $shell @(
                    '-NoProfile', '-File', $fixtureScript, '-Action', 'Test'
                )) 0
            } finally { Pop-Location }
        }
        Assert-Equal (Invoke-External $shell @(
            '-NoProfile', '-File', $fixtureScript, '-Action', 'Verify', '-Timeout', '0'
        )) 1
    } finally {
        # Exact files owned by this test; no recursive deletion or unrelated paths.
        Remove-Item -LiteralPath $fixtureScript -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath (Join-Path $fixtureRoot 'client.py') -Force
        Remove-Item -LiteralPath $fixtureScripts
        Remove-Item -LiteralPath $fixtureRoot
    }
}
Write-Host "All $script:Passed PowerShell checks passed."
