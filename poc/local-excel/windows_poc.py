"""Native Windows preparation and fail-closed OpenCode entry points for local-excel."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import ProxyHandler, build_opener

import poc
import windows_boundary as boundary
import windows_job as job
import windows_ollama as model
import windows_watchdog as watchdog

WORKBOOK_SHA = "9d88b6da7175a8e86188b359cf663b16610cdadeca485a9b773f71bb74858fc4"
LOCK_SHA = "02428609b416acb248ddbf9cde9ca2b9365c8237aff057ad0a9c9e3554d20926"
CHAMBER_PORT = 21435
PROFILES = {"official": "sst-dev.opencode@1.0.0", "chamber": "fedaykindev.openchamber@1.24.2"}
CONTEXT_PROBE = "POC_CONTEXT_ONLY: synthetic Excel environment; no analysis or expected answers.\n"


def tools_at(root, git_root):
    paths = {
        "python_root": root / "python-3.12.12/python",
        "uv_root": root / "uv-0.9.2",
        "opencode_root": root / "opencode-1.19.5",
        "git_root": git_root,
        "code": root / "vscode-1.137.0/Code.exe",
        "ollama": root / "ollama-0.31.1/ollama.exe",
        "uv_cache": root / "uv-cache",
        "profiles": root / "vscode-profiles",
    }
    paths.update(uv=paths["uv_root"] / "uv.exe", python=paths["python_root"] / "python.exe",
                 opencode=paths["opencode_root"] / "opencode.exe", bash=git_root / "bin/bash.exe")
    for key, path in paths.items():
        if not path.exists():
            raise ValueError(f"Missing pinned tool or path: {key}: {path}")
    return {key: str(path.resolve(strict=True)) for key, path in paths.items()}


def environment(run, manifest):
    paths = manifest["paths"]
    system_root = Path(os.environ["SystemRoot"])
    runtime = run / "runtime"
    env = {
        "SystemRoot": str(system_root), "WINDIR": str(system_root),
        "COMSPEC": str(system_root / "System32/cmd.exe"), "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "PATH": os.pathsep.join([str(runtime / "Scripts"), paths["uv_root"],
                                 paths["opencode_root"], str(Path(paths["git_root"]) / "usr/bin"),
                                 str(system_root / "System32")]),
        "HOME": str(run / "home"), "USERPROFILE": str(run / "home"),
        "APPDATA": str(run / "config"), "LOCALAPPDATA": str(run / "state"),
        "TMP": str(run / "tmp"), "TEMP": str(run / "tmp"),
        "XDG_CONFIG_HOME": str(run / "config"), "XDG_CACHE_HOME": str(run / "cache"),
        "XDG_STATE_HOME": str(run / "state"), "XDG_DATA_HOME": str(run / "state"),
        "VIRTUAL_ENV": str(runtime), "UV_PROJECT_ENVIRONMENT": str(runtime),
        "UV_CACHE_DIR": str(run / "cache"), "UV_NO_CONFIG": "1", "UV_PYTHON_DOWNLOADS": "never",
        "UV_LINK_MODE": "copy",
        "PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1",
        "OPENCODE_GIT_BASH_PATH": paths["bash"], "SHELL": paths["bash"],
        "OPENCODE_CONFIG": str(run / "workspace/opencode.json"),
        "OPENCODE_DISABLE_AUTOUPDATE": "true", "OPENCODE_DISABLE_DEFAULT_PLUGINS": "true",
        "OPENCODE_DISABLE_MODELS_FETCH": "true", "OPENCODE_DISABLE_LSP_DOWNLOAD": "true",
    }
    return env


def verify_inputs(run, manifest):
    workspace = run / "workspace"
    for filename, key in (("uv.lock", "lock_sha256"), ("opencode.json", "config_sha256"),
                          ("prompt.txt", "prompt_sha256"), ("context-probe.txt", "context_probe_sha256")):
        path = boundary.safe_path(run, workspace / filename)
        if not path.is_file() or poc.sha256(path) != manifest[key]:
            raise RuntimeError(f"Windows run input changed: {filename}")
    fixture = boundary.safe_path(run, workspace / "銷售 資料/sales.xlsx")
    if manifest["case"] == "missing":
        if fixture.parent.exists():
            raise RuntimeError("Missing-case input directory appeared")
    elif not fixture.is_file() or poc.sha256(fixture) != manifest["fixture_sha256"]:
        raise RuntimeError("Windows fixture changed")
    if (poc.read_json(workspace / "opencode.json") != poc.config(poc.MODEL)
            or manifest["model"] != poc.MODEL or manifest["ollama_url"] != poc.BASE_URL
            or manifest["lock_sha256"] != LOCK_SHA):
        raise RuntimeError("Run config or model differs from the Windows candidate")
    for key, digest in manifest["tool_hashes"].items():
        if poc.sha256(Path(manifest["paths"][key])) != digest:
            raise RuntimeError(f"Windows tool binary changed: {key}")


def prepare(interface, case, runs_root, tools_root, git_root, deadline):
    if deadline.tzinfo is None or deadline <= datetime.now(timezone.utc):
        raise ValueError("Supply a future overall deadline with a time zone")
    if poc.sha256(poc.ROOT / "uv.lock") != LOCK_SHA or poc.sha256(poc.ROOT / "sales.xlsx") != WORKBOOK_SHA:
        raise ValueError("Source workbook or uv.lock differs from the pinned SHA-256")
    paths = tools_at(tools_root, git_root)
    run = poc.prepare(runs_root, case)
    for name in ("home", "config", "state", "cache", "tmp", "evidence", "bin"):
        (run / name).mkdir()
    workspace = run / "workspace"
    (workspace / "context-probe.txt").write_text(CONTEXT_PROBE, encoding="utf-8", newline="\n")
    manifest = poc.read_json(run / "manifest.json")
    manifest.update(
        status="windows-prepared", windows=True, interface=interface, binary=paths["opencode"],
        paths=paths, digest=model.DIGEST, overall_deadline=deadline.isoformat(), ollama_url=poc.BASE_URL,
        python_runtime=str(run / "runtime/Scripts/python.exe"),
        prompt_sha256=poc.sha256(workspace / "prompt.txt"),
        context_probe_sha256=poc.sha256(workspace / "context-probe.txt"),
        tool_hashes={key: poc.sha256(Path(paths[key])) for key in ("python", "uv", "opencode", "bash", "code", "ollama")},
    )
    env = environment(run, manifest)
    setup = {**env, "UV_CACHE_DIR": paths["uv_cache"]}
    command = [paths["uv"], "sync", "--locked", "--offline", "--python", paths["python"]]
    if poc.command(command, run, "uv-sync", 60, setup).returncode:
        raise RuntimeError("Locked Windows setup failed; see uv-sync.stderr")
    command = [manifest["python_runtime"], "-I", "-c",
               "import openpyxl,shutil,sys; assert sys.version_info[:3]==(3,12,12); "
               "assert openpyxl.__version__=='3.1.5'; print(sys.executable); print(shutil.which('python3') or '')"]
    if poc.command(command, run, "python-runtime", 20, env).returncode:
        raise RuntimeError("Pinned Python/openpyxl probe failed")
    version = poc.command([paths["opencode"], "--version"], run, "opencode-version", 15, env)
    if version.returncode or (run / "evidence/opencode-version.stdout").read_text().strip() != "1.19.5":
        raise RuntimeError("Pinned native OpenCode version probe failed")
    manifest["policy_request_sha256"] = boundary.create_request(run, manifest)
    poc.write_json(run / "manifest.json", manifest)
    verify_inputs(run, manifest)
    return run


def checked_run(run, interface=None):
    run = run.resolve(strict=True)
    manifest = poc.read_json(boundary.safe_path(run, run / "manifest.json"))
    if not manifest.get("windows") or (interface is not None and manifest["interface"] != interface):
        raise RuntimeError("Prepare a fresh Windows run for this entry point")
    policy = boundary.require(run, manifest)
    verify_inputs(run, manifest)
    return run, manifest, policy


@contextmanager
def backend_lease(run, manifest):
    lease = model.store(manifest).parent / "evidence/active-opencode.json"
    with lease.open("x", encoding="utf-8") as handle:
        json.dump({"run": run.name, "supervisor_pid": os.getpid()}, handle)
    try:
        yield
    finally:
        lease.unlink()


def guarded_backend(run, interface, args, *, limit=600, port=None, stdio=None):
    run, manifest, policy = checked_run(run, interface)
    with backend_lease(run, manifest):
        return run_backend(run, manifest, policy, args, limit, port, stdio)


def run_backend(run, manifest, policy, args, limit, port, stdio):
    interface = manifest["interface"]
    deadline = watchdog.case_deadline(datetime.fromisoformat(manifest["overall_deadline"]), limit)
    env = environment(run, manifest)
    service, qualification = model.require(manifest)
    if interface == "official":
        env["OPENCODE_CALLER"] = "vscode"
    available = deadline - time.monotonic()
    if available <= 0:
        raise watchdog.GuardStopped("Case deadline reached before effective configuration probe")
    effective = control_command(run, manifest, policy, ["debug", "config"], min(20, available))
    poc.validate_config(effective, poc.MODEL)
    candidate = poc.config(poc.MODEL)
    for key in ("mode", "model", "steps", "temperature", "prompt"):
        if effective["agent"]["excel"].get(key) != candidate["agent"]["excel"][key]:
            raise RuntimeError(f"Effective OpenCode agent differs from candidate: {key}")
    actual_options = effective["provider"]["ollama"]["models"][poc.MODEL]
    if (actual_options.get("options", {}).get("reasoningEffort") != "none"
            or actual_options.get("limit") != {"context": poc.CONTEXT, "output": 8192}):
        raise RuntimeError("Effective OpenCode model options differ from candidate")
    if deadline <= time.monotonic():
        raise watchdog.GuardStopped("Case deadline reached before backend launch")
    workspace = run / "workspace"
    evidence = run / "evidence"
    with (evidence / "started.json").open("x", encoding="utf-8") as started:
        json.dump({"run": run.name, "interface": interface, "started": watchdog.timestamp()}, started)
    poc.write_json(evidence / "qualification.json", qualification)
    poc.write_json(evidence / "effective-config.json", effective)
    cmd = [manifest["binary"], *args]
    try:
        with job.launch(cmd, workspace, env, container_name=policy["container"],
                        container_sid=policy["sid"], stdio=stdio) as process:
            receipt = {
                **process.identity(), "cwd": str(workspace), "run": run.name, "argv": args,
                "config": env["OPENCODE_CONFIG"], "python": manifest["python_runtime"],
                "ollama": poc.BASE_URL, "port": port, "isolation": policy,
            }
            poc.write_json(evidence / "launch.json", receipt)
            code = watchdog.supervise(process, run, env["SystemRoot"], deadline,
                                       ollama=poc.BASE_URL, gui=interface != "cli", port=port,
                                       on_stop=lambda: model.stop(manifest, service),
                                       stop_requested=(evidence / "finish.request").exists,
                                       requested_code=0)
        if code != 124:
            poc.write_json(evidence / "loaded-after.json", poc.api("/api/ps", timeout=5))
        verify_inputs(run, manifest)
        return code
    except BaseException:
        model.stop(manifest, service)
        raise


def run_cli(run, opencode, timeout):
    run, manifest, _ = checked_run(run, "cli")
    # The manifest pins the executable used by every Windows entry point.
    if opencode != "opencode" and Path(opencode).resolve() != Path(manifest["binary"]):
        raise ValueError("CLI binary does not match the Windows manifest")
    evidence = run / "evidence"
    with ((evidence / "opencode-run.stdout").open("xb") as output,
          (evidence / "opencode-run.stderr").open("xb") as errors,
          open(os.devnull, "rb") as stdin):
        prompt = (run / "workspace/prompt.txt").read_text(encoding="utf-8")
        args = ["run", "--format", "json", "--agent", "excel", "--model", f"ollama/{poc.MODEL}", prompt]
        code = guarded_backend(run, "cli", args, limit=min(timeout, 600), stdio=(stdin, output, errors))
    manifest.update(returncode=code, status="recorded" if code == 0 else "failed")
    poc.write_json(run / "manifest.json", manifest)
    return manifest


def official(run, port):
    if not 16384 <= port <= 65535 or os.environ.get("_EXTENSION_OPENCODE_PORT") != str(port):
        raise ValueError("Require the port issued by the pinned official VS Code extension")
    if Path.cwd().resolve() != (run / "workspace").resolve():
        raise ValueError("Official extension started in the wrong workspace")
    return guarded_backend(run, "official", ["--hostname", "127.0.0.1", "--port", str(port),
                           "--agent", "excel", "--model", f"ollama/{poc.MODEL}"], port=port)


def serve(run):
    return guarded_backend(run, "chamber", ["serve", "--hostname", "127.0.0.1",
                           "--port", str(CHAMBER_PORT)], port=CHAMBER_PORT)


def launch_gui(run):
    run, manifest, _ = checked_run(run)
    interface = manifest["interface"]
    if interface not in PROFILES:
        raise ValueError("This run has no VS Code interface")
    watchdog.case_deadline(datetime.fromisoformat(manifest["overall_deadline"]))
    model.require(manifest)
    workspace = run / "workspace"
    paths = manifest["paths"]
    profile = Path(paths["profiles"]) / interface
    flags = ["--user-data-dir", str(profile / "data"), "--extensions-dir", str(profile / "extensions")]
    packages = [poc.read_json(path) for path in (profile / "extensions").glob("*/package.json")]
    versions = [f'{package["publisher"]}.{package["name"]}@{package["version"]}' for package in packages]
    if versions != [PROFILES[interface]]:
        raise RuntimeError("Expected a dedicated VS Code user-data directory with just the pinned extension")
    poc.write_json(run / "evidence/extensions.json", versions)
    settings = {"window.title": f"Excel POC {interface} {manifest['case']} {run.name}",
                "terminal.integrated.cwd": str(workspace), "workbench.startupEditor": "none"}
    if interface == "official":
        launcher = run / "bin/opencode.cmd"
        cmd_paths = [str(sys.executable), str(Path(__file__).resolve()), str(run)]
        if any(c in path for path in cmd_paths for c in ('"', "%", "!", "&", "|", "<", ">", "^", "\n", "\r")):
            raise ValueError("Unsafe path for the Windows extension command shim")
        launcher.write_text(f'@echo off\n"{cmd_paths[0]}" "{cmd_paths[1]}" official "{cmd_paths[2]}" %*\n',
                            encoding="utf-8", newline="\r\n")
        settings.update({
            "terminal.integrated.profiles.windows": {"Excel POC cmd": {"path": os.environ["ComSpec"], "args": ["/d"]}},
            "terminal.integrated.defaultProfile.windows": "Excel POC cmd",
            "terminal.integrated.env.windows": {"PATH": str(run / "bin") + r";${env:PATH}"},
        })
    else:
        receipt_path = run / "evidence/launch.json"
        if not receipt_path.is_file():
            raise RuntimeError("Start the run-scoped OpenChamber backend first")
        backend = poc.read_json(receipt_path)
        if watchdog.listeners(CHAMBER_PORT) != [{"address": "127.0.0.1", "pid": backend["pid"]}]:
            raise RuntimeError("OpenChamber listener differs from the owned backend")
        endpoint = f"http://127.0.0.1:{CHAMBER_PORT}"
        with build_opener(ProxyHandler({})).open(endpoint + "/global/health", timeout=5) as response:
            if json.load(response).get("version") != "1.19.5":
                raise RuntimeError("OpenChamber endpoint is not the pinned backend")
        settings["openchamber.apiUrl"] = endpoint
        settings["openchamber.opencodeBinary"] = str(run / "bin/blocked-unmanaged-backend.exe")
    profile_settings = profile / "data/User/settings.json"
    profile_settings.parent.mkdir(parents=True, exist_ok=True)
    poc.write_json(profile_settings, {"telemetry.telemetryLevel": "off", "update.mode": "none",
                                     "extensions.autoUpdate": False, "extensions.autoCheckUpdates": False})
    location = run / "session.code-workspace"
    poc.write_json(location, {"folders": [{"path": str(workspace)}], "settings": settings})
    child = subprocess.Popen([paths["code"], *flags, "--new-window", str(location)], cwd=workspace)
    poc.write_json(run / "evidence/vscode-launch.json", {"pid": child.pid, "profile": str(profile), "cwd": str(workspace)})


def finish_gui(run):
    run, manifest, _ = checked_run(run)
    if manifest["interface"] not in PROFILES:
        raise ValueError("Only a completed GUI case can request a graceful finish")
    receipt = poc.read_json(run / "evidence/launch.json")
    port, pid = receipt["port"], receipt["pid"]
    if (receipt["run"] != run.name
            or watchdog.listeners(port) != [{"address": "127.0.0.1", "pid": pid}]
            or job.pid_creation_time(pid) != receipt["created_filetime"]):
        raise RuntimeError("No matching active GUI backend to finish")
    (run / "evidence/finish.request").touch(exist_ok=False)


def verify_review_paths(run, manifest):
    run = run.resolve(strict=True)
    verify_inputs(run, manifest)
    for relative in (
        "workspace/analysis.py", "workspace/answer.json", "evidence/python-runtime.stdout",
        "evidence/opencode-run.stdout", "evidence/loaded-after.json", "state/opencode/log/opencode.log",
    ):
        boundary.safe_path(run, run / relative)


def export_session(run, args):
    run, manifest, policy = checked_run(run)
    launch = run / "evidence/launch.json"
    if launch.is_file():
        port = poc.read_json(launch).get("port")
        if port and watchdog.listeners(port):
            raise RuntimeError("Stop the owned OpenCode backend before exporting its session")
    return control_command(run, manifest, policy, args, 30)


def control_command(run, manifest, policy, args, timeout):
    env = environment(run, manifest)
    with (tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr,
          open(os.devnull, "rb") as stdin):
        with job.launch([manifest["binary"], *args], run / "workspace", env,
                        container_name=policy["container"], container_sid=policy["sid"],
                        stdio=(stdin, stdout, stderr)) as process:
            code = process.poll(max(1, int(timeout * 1000)))
            if code is None:
                process.stop()
                raise TimeoutError("OpenCode control command deadline reached")
            if code != 0:
                stderr.seek(0)
                raise RuntimeError(f"OpenCode control command failed ({code}): {stderr.read(1024).decode('utf-8', 'replace')}")
        stdout.seek(0)
        return json.load(stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--interface", choices=("cli", "official", "chamber"), required=True)
    prep.add_argument("--case", choices=("sales", "missing", "corrupt"), default="sales")
    prep.add_argument("--runs-root", required=True, type=Path)
    prep.add_argument("--tools-root", required=True, type=Path)
    prep.add_argument("--git-root", required=True, type=Path)
    prep.add_argument("--deadline", required=True, type=datetime.fromisoformat)
    for name in ("boundary-probe", "serve", "launch", "finish", "official",
                 "serve-ollama", "qualify-model", "stop-ollama"):
        command = sub.add_parser(name)
        command.add_argument("run", type=Path)
        if name == "official":
            command.add_argument("--port", required=True, type=int)
        if name == "boundary-probe":
            command.add_argument("--external-ip", required=True)
            command.add_argument("--external-port", required=True, type=int)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            print(prepare(args.interface, args.case, args.runs_root, args.tools_root, args.git_root, args.deadline))
        elif args.action == "boundary-probe":
            run = args.run.resolve(strict=True)
            manifest = poc.read_json(run / "manifest.json")
            verify_inputs(run, manifest)
            print(json.dumps(boundary.qualify(run, manifest, environment(run, manifest),
                                             external_ip=args.external_ip, external_port=args.external_port)))
        elif args.action in ("serve-ollama", "qualify-model", "stop-ollama"):
            run = args.run.resolve(strict=True)
            manifest = poc.read_json(run / "manifest.json")
            verify_inputs(run, manifest)
            if args.action == "serve-ollama":
                return model.serve(run, manifest)
            if args.action == "qualify-model":
                with backend_lease(run, manifest):
                    print(json.dumps(model.qualify(run, manifest)))
            else:
                model.stop(manifest, model.owner(manifest))
        elif args.action == "serve":
            return serve(args.run)
        elif args.action == "launch":
            launch_gui(args.run)
        elif args.action == "finish":
            finish_gui(args.run)
        else:
            return official(args.run, args.port)
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        print(f"WINDOWS_POC_ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
