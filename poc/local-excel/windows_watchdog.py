"""Run-scoped watchdog. The supervisor owns the Job Object, outside the backend."""

from collections import deque
import ctypes
from ctypes import wintypes as w
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import socket
import subprocess
import threading
import time
from urllib.request import ProxyHandler, build_opener

import windows_job

GIB = 1024 ** 3
INTERVAL = 5
CASE_LIMIT = 600


class PerformanceInfo(ctypes.Structure):
    _fields_ = [("size", w.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            "commit_total", "commit_limit", "commit_peak", "physical_total",
            "physical_available", "system_cache", "kernel_total", "kernel_paged",
            "kernel_nonpaged", "page_size",
        )
    ] + [(name, w.DWORD) for name in ("handles", "processes", "threads")]


class GuardStopped(RuntimeError):
    pass


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sample_power_shell(system_root, since):
    shell = Path(system_root) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    script = r"""
$ErrorActionPreference = 'Stop'
$since = [DateTimeOffset]::Parse('__SINCE__').LocalDateTime
$files = @(Get-CimInstance Win32_PageFileUsage)
$usage = ($files | Measure-Object -Property CurrentUsage -Sum).Sum
$errors = @()
foreach ($provider in 'Display','Microsoft-Windows-DxgKrnl','igfx','igfxn') {
    try {
        $errors += @(Get-WinEvent -FilterHashtable @{
            LogName='System'; ProviderName=$provider; Level=1,2,3; StartTime=$since
        } -MaxEvents 1 -ErrorAction Stop)
    } catch {
        if ($_.FullyQualifiedErrorId -notmatch '^(NoMatchingEventsFound|NoMatchingProvidersFound|LogsAndProvidersDontOverlap),') {
            throw
        }
    }
}
@{pagefile_mib=[int]$usage; gpu_error=@($errors | ForEach-Object {
  @{id=$_.Id; provider=$_.ProviderName; record=$_.RecordId}
})} | ConvertTo-Json -Compress -Depth 3
""".replace("__SINCE__", since)
    result = subprocess.run(
        [str(shell), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, timeout=4, check=True, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return json.loads(result.stdout)


def sample(system_root, runs_root, since):
    info = PerformanceInfo()
    info.size = ctypes.sizeof(info)
    library = ctypes.WinDLL("psapi", use_last_error=True)
    get_info = windows_job.bind(library, "GetPerformanceInfo", w.BOOL,
                                ctypes.POINTER(PerformanceInfo), w.DWORD)
    windows_job.require(get_info(ctypes.byref(info), info.size))
    page = info.page_size
    return {
        "time": timestamp(),
        "available_ram": info.physical_available * page,
        "commit_headroom": (info.commit_limit - info.commit_total) * page,
        "system_disk_free": shutil.disk_usage(Path(system_root).anchor).free,
        "runs_disk_free": shutil.disk_usage(runs_root).free,
        **sample_power_shell(system_root, since),
    }


def append(path, record):
    with path.open("a", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(record, ensure_ascii=False) + "\n")


def case_deadline(overall, limit=CASE_LIMIT):
    remaining = (overall - datetime.now(timezone.utc)).total_seconds()
    if remaining <= 0 or not 0 < limit <= CASE_LIMIT:
        raise GuardStopped("Run deadline expired or invalid case limit")
    return time.monotonic() + min(limit, remaining)


def admit(system_root, runs_root, evidence, deadline):
    """Require seven consecutive samples across at least thirty seconds."""
    since = timestamp()
    started = time.monotonic()
    for index in range(7):
        delay = started + index * INTERVAL - time.monotonic()
        if delay > 0:
            if time.monotonic() + delay >= deadline:
                raise GuardStopped("Deadline reached before thirty-second resource admission")
            time.sleep(delay)
        if time.monotonic() >= deadline:
            raise GuardStopped("Deadline reached before resource admission")
        snapshot = sample(system_root, runs_root, since)
        append(evidence, {"phase": "admission", **snapshot})
        if (snapshot["available_ram"] < 10 * GIB or snapshot["commit_headroom"] < 12 * GIB
                or snapshot["system_disk_free"] < 10 * GIB or snapshot["runs_disk_free"] < 25 * GIB):
            raise GuardStopped("Resource admission floor not met")
        if snapshot["gpu_error"]:
            raise GuardStopped("Display or GPU driver error during resource admission")


class ResourceStops:
    def __init__(self):
        self.low_ram = 0
        self.low_commit = 0
        self.pagefile = deque()

    def observe(self, now, snapshot):
        self.low_ram = self.low_ram + 1 if snapshot["available_ram"] <= 4 * GIB else 0
        self.low_commit = self.low_commit + 1 if snapshot["commit_headroom"] <= 6 * GIB else 0
        while self.pagefile and now - self.pagefile[0][0] > 30:
            self.pagefile.popleft()
        usage = snapshot["pagefile_mib"]
        fast_growth = any(usage - previous >= 512 for _, previous in self.pagefile)
        self.pagefile.append((now, usage))
        if self.low_ram >= 2 or self.low_commit >= 2:
            return "RAM or commit stop floor reached"
        if fast_growth:
            return "Pagefile grew by at least 512 MiB within thirty seconds"
        if snapshot["gpu_error"]:
            return "New display or GPU driver error"
        return None


def windows_for_run(run_id):
    user = ctypes.WinDLL("user32", use_last_error=True)
    enum_callback = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    enumerate_windows = windows_job.bind(user, "EnumWindows", w.BOOL, enum_callback, w.LPARAM)
    window_text = windows_job.bind(user, "GetWindowTextW", ctypes.c_int, w.HWND, w.LPWSTR, ctypes.c_int)
    is_hung = windows_job.bind(user, "IsHungAppWindow", w.BOOL, w.HWND)
    result = []

    @enum_callback
    def inspect_window(handle, _):
        title = ctypes.create_unicode_buffer(512)
        if window_text(handle, title, len(title)) and run_id in title.value and "Excel POC" in title.value:
            result.append({"handle": handle, "hung": bool(is_hung(handle))})
        return True

    windows_job.require(enumerate_windows(inspect_window, 0))
    return result


class IPv4Row(ctypes.Structure):
    _fields_ = [(name, w.DWORD) for name in (
        "state", "address", "port", "remote_address", "remote_port", "pid",
    )]


class IPv6Row(ctypes.Structure):
    _fields_ = [
        ("address", ctypes.c_ubyte * 16), ("scope", w.DWORD), ("port", w.DWORD),
        ("remote_address", ctypes.c_ubyte * 16), ("remote_scope", w.DWORD),
        ("remote_port", w.DWORD), ("state", w.DWORD), ("pid", w.DWORD),
    ]


def listeners(port):
    library = ctypes.WinDLL("iphlpapi")
    table = windows_job.bind(library, "GetExtendedTcpTable", w.DWORD, ctypes.c_void_p,
                             ctypes.POINTER(w.DWORD), w.BOOL, w.ULONG, ctypes.c_int, w.ULONG)
    result = []
    for family, row_type in ((socket.AF_INET, IPv4Row), (socket.AF_INET6, IPv6Row)):
        size = w.DWORD()
        table(None, ctypes.byref(size), False, family, 3, 0)
        for _ in range(3):
            data = ctypes.create_string_buffer(size.value)
            error = table(data, ctypes.byref(size), False, family, 3, 0)
            if error != 122:
                break
        if error:
            raise ctypes.WinError(error)
        count = w.DWORD.from_buffer(data).value
        rows = (row_type * count).from_buffer(data, ctypes.sizeof(w.DWORD))
        for row in rows:
            if socket.ntohs(row.port & 0xffff) == port:
                packed = row.address.to_bytes(4, "little") if family == socket.AF_INET else bytes(row.address)
                result.append({"address": socket.inet_ntop(family, packed), "pid": row.pid})
    return result


def supervise(process, run, system_root, deadline, *, ollama=None, gui=False, port=None,
              health_path="/global/health", stop_requested=None, cwd=None, on_stop=None,
              requested_code=124):
    """Monitor host resources and terminate the owned Job even during a slow sample."""
    evidence = run / "evidence"
    since = timestamp()
    resource_stops = ResourceStops()
    opener = build_opener(ProxyHandler({}))
    next_sample = time.monotonic()
    service_deadline = next_sample + 20
    failures = {}
    hung_since = None
    reason = "backend exited"
    code = 125
    identity = process.identity()
    expired = threading.Event()
    requested = threading.Event()
    done = threading.Event()

    def stop_at_deadline():
        expired.set()
        process.stop(124)
        if on_stop is not None:
            on_stop()

    def poll_stop_request():
        while not done.wait(0.1):
            if stop_requested():
                requested.set()
                process.stop(requested_code)
                return

    timer = threading.Timer(max(0, deadline - time.monotonic()), stop_at_deadline)
    timer.daemon = True
    timer.start()
    request_thread = None
    if stop_requested is not None:
        request_thread = threading.Thread(target=poll_stop_request, daemon=True)
        request_thread.start()
    try:
        while True:
            now = time.monotonic()
            if now >= deadline or expired.is_set():
                raise GuardStopped("Case or overall deadline reached")
            if requested.is_set():
                reason = "Evaluator requested the owned Job stop"
                code = requested_code
                return code
            result = process.poll(min(250, max(1, int((deadline - now) * 1000))))
            if result is not None:
                if expired.is_set():
                    raise GuardStopped("Case or overall deadline reached")
                if requested.is_set():
                    reason = "Evaluator requested the owned Job stop"
                    code = requested_code
                    return code
                code = result
                return code
            if now < next_sample:
                continue
            next_sample = now + INTERVAL
            snapshot = sample(system_root, run.parent, since)
            windows = windows_for_run(run.name) if gui else []
            if any(window["hung"] for window in windows):
                hung_since = now if hung_since is None else hung_since
            else:
                hung_since = None
            reason = resource_stops.observe(now, snapshot)
            sockets = listeners(port) if port else []
            append(evidence / "resources.jsonl", {
                "phase": "running", **snapshot, "windows": windows, "listeners": sockets,
            })
            if reason:
                raise GuardStopped(reason)
            if hung_since is not None and now - hung_since >= 15:
                raise GuardStopped("POC window unresponsive for fifteen seconds")
            health = [ollama + "/api/version"] if ollama else []
            if port:
                if sockets == [{"address": "127.0.0.1", "pid": identity["pid"]}]:
                    health.append(f"http://127.0.0.1:{port}{health_path}")
                elif sockets or now >= service_deadline:
                    raise GuardStopped("Backend listener is unavailable or differs from the owned loopback socket")
            for url in health:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise GuardStopped("Deadline reached before health sampling")
                try:
                    with opener.open(url, timeout=min(5, remaining)) as response:
                        response.read(4096)
                except OSError:
                    failures[url] = failures.get(url, 0) + 1
                else:
                    failures[url] = 0
                if failures[url] >= 2:
                    raise GuardStopped(f"Two consecutive health checks failed for {url}")
    except GuardStopped as error:
        reason = str(error)
        code = 124
        if not expired.is_set() and not requested.is_set():
            process.stop(code)
            if on_stop is not None:
                on_stop()
        return code
    except BaseException as error:
        reason = f"Watchdog evidence unavailable: {error}"
        process.stop(code)
        raise
    finally:
        done.set()
        if request_thread is not None:
            request_thread.join()
        timer.cancel()
        timer.join()
        append(evidence / "stops.jsonl", {
            **identity, "cwd": str(cwd if cwd is not None else run / "workspace"), "ollama": ollama, "port": port,
            "time": timestamp(), "reason": reason or "backend exited", "exit": code,
        })
