"""Prepare a run-scoped policy request and qualify an externally provisioned boundary."""

import _winapi
import ctypes
from ctypes import wintypes as w
import ipaddress
import json
import os
from pathlib import Path
import socket
import stat

import poc
import windows_job

KIND = "windows-appcontainer-wfp-job"
POLICY_ERROR = "Windows boundary requires an approved AppContainer and a successful same-run probe"


def safe_path(root, path):
    """Evidence collection must not follow an agent-created reparse point."""
    root = root.resolve(strict=True)
    path = Path(path)
    relative = path.relative_to(root)
    if ".." in relative.parts:
        raise ValueError("Run path traverses outside its root")
    current = root
    for component in relative.parts:
        current /= component
        try:
            entry = current.lstat()
        except FileNotFoundError:
            continue
        if entry.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"Unexpected reparse point in run: {current}")
    return path


def create_request(run, manifest):
    paths = manifest["paths"]
    request = {
        "kind": KIND,
        "run": run.name,
        "container": f"LocalExcelPoc.{run.name}",
        "read_execute": [
            paths["python_root"], paths["uv_root"], paths["opencode_root"],
            paths["git_root"], str(run / "runtime"),
        ],
        "read_write": [str(run / name) for name in ("workspace", "home", "state", "cache", "config", "tmp")],
        "deny_access": [str(poc.REPO_ROOT), str(run / "evidence")],
        "deny_other_runs_and_parent_enumeration": str(run.parent),
        "outbound": {"address": "127.0.0.1", "port": 21434, "protocol": "TCP"},
        "ollama_service": {"image": paths["ollama"], "listen": "127.0.0.1", "port": 21434,
                           "deny_outbound_during_validation": True},
        "api": {
            "image": paths["opencode"],
            "listen": "127.0.0.1",
            "ports": {"official": [16384, 65535], "chamber": [21435, 21435]}.get(manifest["interface"]),
        },
    }
    poc.write_json(run / "policy-request.json", request)
    return poc.sha256(run / "policy-request.json")


def check_active_filters(filter_ids):
    if (not isinstance(filter_ids, list) or not filter_ids
            or any(type(value) is not int or not 0 < value < 2 ** 64 for value in filter_ids)):
        raise RuntimeError("Provisioning receipt must specify active Windows filtering IDs")
    library = ctypes.WinDLL("fwpuclnt")
    open_engine = windows_job.bind(library, "FwpmEngineOpen0", w.DWORD,
                                   w.LPCWSTR, w.UINT, ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.POINTER(w.HANDLE))
    close_engine = windows_job.bind(library, "FwpmEngineClose0", w.DWORD, w.HANDLE)
    find_filter = windows_job.bind(library, "FwpmFilterGetById0", w.DWORD, w.HANDLE,
                                   ctypes.c_uint64, ctypes.POINTER(ctypes.c_void_p))
    free = windows_job.bind(library, "FwpmFreeMemory0", None, ctypes.POINTER(ctypes.c_void_p))
    engine = w.HANDLE()
    result = open_engine(None, 10, None, None, ctypes.byref(engine))
    if result:
        raise RuntimeError(f"Cannot verify active WFP policy (0x{result:08x})")
    try:
        for identifier in filter_ids:
            item = ctypes.c_void_p()
            result = find_filter(engine, identifier, ctypes.byref(item))
            if result or not item:
                raise RuntimeError(f"Provisioned WFP filter {identifier} unavailable (0x{result:08x})")
            free(ctypes.byref(item))
    finally:
        close_engine(engine)


def provisioned(run, manifest):
    request = safe_path(run, run / "policy-request.json")
    policy = safe_path(run, run / "provisioned-policy.json")
    if (not request.is_file() or poc.sha256(request) != manifest["policy_request_sha256"]
            or not policy.is_file()):
        raise RuntimeError(POLICY_ERROR)
    document = poc.read_json(request)
    provision = poc.read_json(policy)
    expected = {key: document[key] for key in ("kind", "run", "container")}
    expected["request_sha256"] = manifest["policy_request_sha256"]
    if (any(provision.get(key) != value for key, value in expected.items())
            or not isinstance(provision.get("sid"), str)
            or not provision.get("wfp_filter_ids")):
        raise RuntimeError(POLICY_ERROR)
    with windows_job.appcontainer_sid(expected["container"]) as sid:
        if provision["sid"] != windows_job.sid_text(sid):
            raise RuntimeError("Policy SID does not match the run AppContainer")
    for field in ("wfp_filter_ids", "ollama_wfp_filter_ids"):
        check_active_filters(provision.get(field))
    return provision


def require(run, manifest):
    policy = provisioned(run, manifest)
    receipt_path = safe_path(run, run / "evidence/boundary-probe.json")
    if not receipt_path.is_file():
        raise RuntimeError(POLICY_ERROR)
    receipt = poc.read_json(receipt_path)
    if (receipt.get("status") != "passed" or receipt.get("run") != run.name
            or receipt.get("policy_sha256") != poc.sha256(run / "provisioned-policy.json")
            or receipt.get("request_sha256") != manifest["policy_request_sha256"]):
        raise RuntimeError(POLICY_ERROR)
    return policy


# The probe uses synthetic markers and the exact launcher/token used by OpenCode.
# It contains no analysis implementation or oracle data.
CHECKS = r"""
import json, socket, sys
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

settings = json.loads(sys.argv[1])
for forbidden in settings["denied_files"]:
    try:
        with open(forbidden, "rb"):
            pass
    except OSError as error:
        if error.winerror not in (2, 3, 5):
            raise
    else:
        raise AssertionError("forbidden control checkout file opened")
for root in settings["canaries"]:
    root = Path(root)
    for read in (lambda: list(root.iterdir()), lambda: (root / "canary.txt").read_bytes()):
        try:
            read()
        except OSError as error:
            if error.winerror not in (2, 3, 5):
                raise
        else:
            raise AssertionError("forbidden canary read or enumeration: " + str(root))
for target in settings["denied_network"]:
    try:
        with socket.create_connection(tuple(target), timeout=2):
            raise AssertionError("unauthorized TCP connect: " + str(target))
    except OSError as error:
        if error.winerror != 10013 and not isinstance(error, TimeoutError):
            raise
with build_opener(ProxyHandler({})).open(settings["allow"] + "/api/version", timeout=2) as response:
    if json.load(response)["version"] != "0.31.1":
        raise AssertionError("unexpected Ollama identity")
"""

PROBE = CHECKS + r"""
import os
import subprocess
import openpyxl
if openpyxl.__version__ != "3.1.5" or sys.version_info[:3] != (3, 12, 12):
    raise AssertionError("unexpected Python / openpyxl version")
marker = Path("probe-marker.txt")
marker.write_text("無答案", encoding="utf-8")
if marker.read_text(encoding="utf-8") != "無答案":
    raise AssertionError("workspace read/write failed")
marker.unlink()
bash = os.environ["OPENCODE_GIT_BASH_PATH"]
result = subprocess.run([bash, "--noprofile", "--norc", "-c",
    "uv run --locked --offline python -c 'import sys,openpyxl; print(sys.executable); print(openpyxl.__version__)'"],
    check=True, timeout=10, capture_output=True, encoding="utf-8")
runtime, version = result.stdout.strip().splitlines()
if Path(runtime) != Path(sys.executable) or version != "3.1.5":
    raise AssertionError("Git Bash resolved a different locked runtime")
subprocess.run([sys.executable, "-I", "-c", settings["child"], sys.argv[1]], check=True, timeout=20)
print(json.dumps({"workspace_write": True, "child_checks": True, "interpreter": sys.executable}))
"""


def qualify(run, manifest, env, *, external_ip, external_port):
    """Called only after the run's OS policy and approved test endpoint exist."""
    policy = provisioned(run, manifest)
    workspace = run / "workspace"
    evidence = run / "evidence"
    if (evidence / "boundary-probe.json").exists():
        raise RuntimeError("Use a fresh run for another boundary probe")
    if not ipaddress.ip_address(external_ip).is_global or not 0 < external_port < 65536:
        raise ValueError("Use the externally reachable TCP control approved for this experiment")
    # Positive control avoids accepting an already-unreachable endpoint as a denial.
    with socket.create_connection((external_ip, external_port), timeout=3):
        pass
    evaluator_canary = evidence / "evaluator-canary"
    sibling = run.parent / f"outside-{run.name}"
    for directory in (evaluator_canary, sibling):
        directory.mkdir()
        (directory / "canary.txt").write_text("NO_ANSWERS", encoding="ascii")
    junction = workspace / "boundary-reparse"
    _winapi.CreateJunction(str(evaluator_canary), str(junction))
    try:
        with socket.socket() as deny_listener:
            deny_listener.bind(("127.0.0.1", 0))
            deny_listener.listen()
            with socket.create_connection(deny_listener.getsockname(), timeout=2):
                pass
            settings = {
                "canaries": [str(p) for p in (evaluator_canary, sibling, junction, poc.REPO_ROOT)],
                "denied_files": [str(poc.REPO_ROOT / "README.md")],
                "denied_network": [list(deny_listener.getsockname()), [external_ip, external_port]],
                "allow": poc.BASE_URL, "child": CHECKS,
            }
            with ((evidence / "boundary.stdout").open("wb") as output,
                  (evidence / "boundary.stderr").open("wb") as errors,
                  open(os.devnull, "rb") as input_stream):
                argv = [str(run / "runtime/Scripts/python.exe"), "-I", "-c", PROBE, json.dumps(settings)]
                with windows_job.launch(argv, workspace, env, container_name=policy["container"],
                                        container_sid=policy["sid"], stdio=(input_stream, output, errors)) as process:
                    identity = process.identity()
                    result = process.poll(30000)
                    if result is None:
                        process.stop()
                        raise TimeoutError("Windows boundary probe timed out")
                    if result != 0:
                        raise RuntimeError(f"Windows boundary probe failed ({result}); see boundary.stderr")
    finally:
        # rmdir removes only this junction, never its target.
        junction.rmdir()
    result = poc.read_json(evidence / "boundary.stdout")
    if (result.get("child_checks") is not True or result.get("workspace_write") is not True
            or Path(result.get("interpreter", "")) != run / "runtime/Scripts/python.exe"):
        raise RuntimeError("Boundary probe did not return the required runtime evidence")
    receipt = {
        "status": "passed", "run": run.name, **identity, **result,
        "request_sha256": manifest["policy_request_sha256"],
        "policy_sha256": poc.sha256(run / "provisioned-policy.json"),
    }
    poc.write_json(evidence / "boundary-probe.json", receipt)
    return receipt
