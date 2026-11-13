"""Native Windows process containment. Policy provisioning is external to this module."""

from contextlib import ExitStack, contextmanager
import ctypes
from ctypes import wintypes as w
import msvcrt
import subprocess
import sys

kernel = ctypes.WinDLL("kernel32", use_last_error=True)
advapi = ctypes.WinDLL("advapi32", use_last_error=True)
userenv = ctypes.WinDLL("userenv", use_last_error=True)
ptr = ctypes.c_void_p
size = ctypes.c_size_t


class BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("per_process_time", ctypes.c_int64), ("per_job_time", ctypes.c_int64),
        ("limit_flags", w.DWORD), ("minimum_working_set", size),
        ("maximum_working_set", size), ("active_process_limit", w.DWORD),
        ("affinity", size), ("priority_class", w.DWORD), ("scheduling_class", w.DWORD),
    ]


class ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("basic", BasicLimitInformation), ("io_counters", ctypes.c_uint64 * 6),
        ("process_memory_limit", size), ("job_memory_limit", size),
        ("peak_process_memory_used", size), ("peak_job_memory_used", size),
    ]


class StartupInfo(ctypes.Structure):
    _fields_ = [
        ("cb", w.DWORD), ("reserved", w.LPWSTR), ("desktop", w.LPWSTR),
        ("title", w.LPWSTR), ("x", w.DWORD), ("y", w.DWORD),
        ("x_size", w.DWORD), ("y_size", w.DWORD), ("x_count_chars", w.DWORD),
        ("y_count_chars", w.DWORD), ("fill_attribute", w.DWORD), ("flags", w.DWORD),
        ("show_window", w.WORD), ("reserved_size", w.WORD), ("reserved_data", ptr),
        ("stdin", w.HANDLE), ("stdout", w.HANDLE), ("stderr", w.HANDLE),
    ]


class StartupInfoEx(ctypes.Structure):
    _fields_ = [("startup", StartupInfo), ("attributes", ptr)]


class ProcessInformation(ctypes.Structure):
    _fields_ = [
        ("process", w.HANDLE), ("thread", w.HANDLE),
        ("pid", w.DWORD), ("thread_id", w.DWORD),
    ]


class SecurityCapabilities(ctypes.Structure):
    _fields_ = [
        ("sid", ptr), ("capabilities", ptr),
        ("capability_count", w.DWORD), ("reserved", w.DWORD),
    ]


def bind(dll, name, result, *args):
    function = getattr(dll, name)
    function.restype = result
    function.argtypes = args
    return function


close = bind(kernel, "CloseHandle", w.BOOL, w.HANDLE)
create_job = bind(kernel, "CreateJobObjectW", w.HANDLE, ptr, w.LPCWSTR)
set_job = bind(kernel, "SetInformationJobObject", w.BOOL, w.HANDLE, ctypes.c_int, ptr, w.DWORD)
assign_job = bind(kernel, "AssignProcessToJobObject", w.BOOL, w.HANDLE, w.HANDLE)
in_job = bind(kernel, "IsProcessInJob", w.BOOL, w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL))
terminate_job = bind(kernel, "TerminateJobObject", w.BOOL, w.HANDLE, w.UINT)
terminate_process = bind(kernel, "TerminateProcess", w.BOOL, w.HANDLE, w.UINT)
current_process = bind(kernel, "GetCurrentProcess", w.HANDLE)
open_process = bind(kernel, "OpenProcess", w.HANDLE, w.DWORD, w.BOOL, w.DWORD)
duplicate_handle = bind(kernel, "DuplicateHandle", w.BOOL, w.HANDLE, w.HANDLE, w.HANDLE,
                        ctypes.POINTER(w.HANDLE), w.DWORD, w.BOOL, w.DWORD)
init_attributes = bind(kernel, "InitializeProcThreadAttributeList", w.BOOL, ptr, w.DWORD,
                       w.DWORD, ctypes.POINTER(size))
update_attribute = bind(kernel, "UpdateProcThreadAttribute", w.BOOL, ptr, w.DWORD, size,
                        ptr, size, ptr, ptr)
delete_attributes = bind(kernel, "DeleteProcThreadAttributeList", None, ptr)
create_process = bind(kernel, "CreateProcessW", w.BOOL, w.LPCWSTR, w.LPWSTR, ptr, ptr, w.BOOL,
                      w.DWORD, ptr, w.LPCWSTR, ctypes.POINTER(StartupInfoEx),
                      ctypes.POINTER(ProcessInformation))
resume = bind(kernel, "ResumeThread", w.DWORD, w.HANDLE)
wait = bind(kernel, "WaitForSingleObject", w.DWORD, w.HANDLE, w.DWORD)
exit_code = bind(kernel, "GetExitCodeProcess", w.BOOL, w.HANDLE, ctypes.POINTER(w.DWORD))
process_times = bind(kernel, "GetProcessTimes", w.BOOL, w.HANDLE, *([ctypes.POINTER(w.FILETIME)] * 4))
open_token = bind(advapi, "OpenProcessToken", w.BOOL, w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE))
token_info = bind(advapi, "GetTokenInformation", w.BOOL, w.HANDLE, ctypes.c_int, ptr, w.DWORD,
                  ctypes.POINTER(w.DWORD))
equal_sid = bind(advapi, "EqualSid", w.BOOL, ptr, ptr)
string_sid = bind(advapi, "ConvertSidToStringSidW", w.BOOL, ptr, ctypes.POINTER(w.LPWSTR))
local_free = bind(kernel, "LocalFree", ptr, ptr)
derive_sid = bind(userenv, "DeriveAppContainerSidFromAppContainerName", w.LONG, w.LPCWSTR,
                  ctypes.POINTER(ptr))
free_sid = bind(advapi, "FreeSid", ptr, ptr)

JOB_EXTENDED_LIMIT_INFORMATION = 9
JOB_KILL_ON_CLOSE = 0x2000
ATTRIBUTE_HANDLE_LIST = 0x00020002
ATTRIBUTE_SECURITY_CAPABILITIES = 0x00020009
STARTF_USESTDHANDLES = 0x100
CREATE_SUSPENDED = 0x4
CREATE_UNICODE_ENVIRONMENT = 0x400
EXTENDED_STARTUPINFO_PRESENT = 0x80000
TOKEN_QUERY = 0x8
TOKEN_APP_CONTAINER_SID = 31
DUPLICATE_SAME_ACCESS = 0x2
WAIT_TIMEOUT = 0x102


def require(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


@contextmanager
def appcontainer_sid(name):
    sid = ptr()
    result = derive_sid(name, ctypes.byref(sid))
    if result or not sid:
        raise OSError(f"DeriveAppContainerSidFromAppContainerName failed (HRESULT 0x{result & 0xffffffff:08x})")
    try:
        yield sid
    finally:
        free_sid(sid)


def sid_text(sid):
    address = w.LPWSTR()
    require(string_sid(sid, ctypes.byref(address)))
    try:
        return address.value
    finally:
        local_free(ctypes.cast(address, ptr))


def check_token(process, expected_sid):
    token = w.HANDLE()
    require(open_token(process, TOKEN_QUERY, ctypes.byref(token)))
    try:
        count = w.DWORD()
        token_info(token, TOKEN_APP_CONTAINER_SID, None, 0, ctypes.byref(count))
        require(count.value)
        buffer = ctypes.create_string_buffer(count.value)
        require(token_info(token, TOKEN_APP_CONTAINER_SID, buffer, count, ctypes.byref(count)))
        actual = ctypes.cast(buffer, ctypes.POINTER(ptr))[0]
        if not actual or not equal_sid(actual, expected_sid):
            raise RuntimeError("Child token does not match the provisioned AppContainer SID")
    finally:
        close(token)


def creation_time(handle):
    created, exited, kernel_time, user_time = (w.FILETIME() for _ in range(4))
    require(process_times(handle, ctypes.byref(created), ctypes.byref(exited),
                          ctypes.byref(kernel_time), ctypes.byref(user_time)))
    return created.dwHighDateTime << 32 | created.dwLowDateTime


def pid_creation_time(pid):
    handle = require(open_process(0x1000, False, pid))  # PROCESS_QUERY_LIMITED_INFORMATION
    try:
        return creation_time(handle)
    finally:
        close(handle)


def is_live(identity):
    handle = open_process(0x101000, False, identity["pid"])  # SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION
    if not handle and ctypes.get_last_error() == 87:  # ERROR_INVALID_PARAMETER for an exited PID
        return False
    require(handle)
    try:
        if creation_time(handle) != identity["created_filetime"]:
            return False
        state = wait(handle, 0)
        if state == 0:
            return False
        if state != WAIT_TIMEOUT:
            raise ctypes.WinError(ctypes.get_last_error())
        return True
    finally:
        close(handle)


class ManagedProcess:
    def __init__(self, info, job):
        self.info = info
        self.job = job

    def identity(self):
        return {"pid": self.info.pid, "created_filetime": creation_time(self.info.process)}

    def poll(self, milliseconds=0):
        state = wait(self.info.process, milliseconds)
        if state == WAIT_TIMEOUT:
            return None
        if state != 0:
            raise ctypes.WinError(ctypes.get_last_error())
        code = w.DWORD()
        require(exit_code(self.info.process, ctypes.byref(code)))
        return code.value

    def stop(self, code=124):
        require(terminate_job(self.job, code))


@contextmanager
def launch(argv, cwd, env, *, container_name=None, container_sid=None, stdio=None):
    """Start suspended, pin process/job handles, check the token, then resume."""
    if bool(container_name) != bool(container_sid):
        raise ValueError("AppContainer name and SID must be supplied together")
    with ExitStack() as stack:
        job = require(create_job(None, None))
        stack.callback(close, job)
        limits = ExtendedLimitInformation()
        limits.basic.limit_flags = JOB_KILL_ON_CLOSE
        require(set_job(job, JOB_EXTENDED_LIMIT_INFORMATION, ctypes.byref(limits), ctypes.sizeof(limits)))

        attr_count = 1 + bool(container_name)
        attribute_size = size()
        init_attributes(None, attr_count, 0, ctypes.byref(attribute_size))
        require(attribute_size.value)
        attributes = ctypes.create_string_buffer(attribute_size.value)
        require(init_attributes(attributes, attr_count, 0, ctypes.byref(attribute_size)))
        stack.callback(delete_attributes, attributes)
        startup = StartupInfoEx()
        startup.startup.cb = ctypes.sizeof(startup)
        startup.startup.flags = STARTF_USESTDHANDLES
        startup.attributes = ctypes.cast(attributes, ptr)
        handles = (w.HANDLE * 3)()
        own = current_process()
        for index, stream in enumerate(stdio or (sys.stdin, sys.stdout, sys.stderr)):
            target = w.HANDLE()
            require(duplicate_handle(own, msvcrt.get_osfhandle(stream.fileno()), own,
                                     ctypes.byref(target), 0, True, DUPLICATE_SAME_ACCESS))
            handles[index] = target.value
            stack.callback(close, target)
        startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = handles
        require(update_attribute(attributes, 0, ATTRIBUTE_HANDLE_LIST, handles,
                                 ctypes.sizeof(handles), None, None))

        if container_name:
            sid = stack.enter_context(appcontainer_sid(container_name))
            if sid_text(sid) != container_sid:
                raise RuntimeError("Provisioned SID differs from the run AppContainer")
            capabilities = SecurityCapabilities(sid, None, 0, 0)
            require(update_attribute(attributes, 0, ATTRIBUTE_SECURITY_CAPABILITIES,
                                     ctypes.byref(capabilities), ctypes.sizeof(capabilities), None, None))

        info = ProcessInformation()
        command = ctypes.create_unicode_buffer(subprocess.list2cmdline([str(arg) for arg in argv]))
        variables = ctypes.create_unicode_buffer(
            "\0".join(f"{key}={value}" for key, value in sorted(env.items(), key=lambda item: item[0].upper())) + "\0")
        require(create_process(str(argv[0]), command, None, None, True,
                               CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT | EXTENDED_STARTUPINFO_PRESENT,
                               variables, str(cwd), ctypes.byref(startup), ctypes.byref(info)))
        stack.callback(close, info.process)
        stack.callback(close, info.thread)
        try:
            require(assign_job(job, info.process))
            member = w.BOOL()
            require(in_job(info.process, job, ctypes.byref(member)))
            require(member.value)
            if container_name:
                check_token(info.process, sid)
            if resume(info.thread) == 0xffffffff:
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            terminate_process(info.process, 125)
            raise
        yield ManagedProcess(info, job)
