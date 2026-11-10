"""Mac-only experimental execution boundary qualified by E004.

The profile applies to OpenCode and all descendants. It is not a general
hostile-code security guarantee; Apple has deprecated sandbox-exec.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import platform
import subprocess
import poc

SANDBOX = '/usr/bin/sandbox-exec'
BOUNDARY = 'mac-seatbelt-e004-v1'


def environment(run: Path) -> dict[str, str]:
    env = poc.environment(run)
    env.update(TMPDIR=str(run / 'tmp') + '/', TMP=str(run / 'tmp'), TEMP=str(run / 'tmp'),
               TMPPREFIX=str(run / 'tmp/zsh'))
    return env


def runtime_roots(run: Path, binary: str) -> list[str]:
    python_root = (run / 'workspace/.venv/bin/python').resolve().parent.parent
    if not python_root.name.startswith('cpython-3.12.12-'):
        raise ValueError('unqualified Python runtime root')
    binary_path = Path(binary).resolve()
    tool_root = next((p.parent for p in binary_path.parents if p.name == 'node_modules'), None)
    if tool_root is None or tool_root == poc.REPO_ROOT or poc.REPO_ROOT in tool_root.parents or run.is_relative_to(tool_root):
        raise ValueError('OpenCode must use a separate npm runtime tree')
    return ['/bin', '/sbin', '/usr/bin', '/usr/sbin', '/opt/homebrew', str(python_root), str(tool_root)]


def profile(run: Path, binary: str) -> str:
    roots = runtime_roots(run, binary)
    rw = [str(run / n) for n in ['workspace', 'tmp', 'config', 'cache', 'state']]
    return '''(version 1)
(deny default)
(import "system.sb")
(allow syscall* mach-bootstrap process-exec process-fork sysctl-read)
(allow process-info* (target same-sandbox))
(allow signal (target same-sandbox))
(allow file-read-metadata file-test-existence)
(allow mach-lookup (global-name "com.apple.bsd.dirhelper") (global-name "com.apple.system.opendirectoryd.libinfo") (global-name "com.apple.SystemConfiguration.configd"))
(allow file-read* file-map-executable
''' + ''.join(' (subpath ' + json.dumps(p) + ')\n' for p in roots) + ')\n(allow file-read* file-write* file-map-executable\n' + ''.join(' (subpath ' + json.dumps(p) + ')\n' for p in rw) + ''')
(allow file-read* file-write* file-ioctl (subpath "/dev"))
(allow file-read-data (literal "/private/etc/hosts") (literal "/private/etc/resolv.conf") (literal "/private/etc/apache2/mime.types"))
(allow network-outbound (remote ip "localhost:11434"))
(allow network-bind network-inbound (local ip "localhost:*"))

; Exact OS resolver endpoints, based on installed Apple service profiles.
(allow mach-lookup (global-name "com.apple.SystemConfiguration.DNSConfiguration") (global-name "com.apple.dnssd.service"))
(allow network-outbound (literal "/private/var/run/mDNSResponder"))
'''


def prepare(run: Path, binary: str) -> dict:
    if platform.system() != 'Darwin' or not Path(SANDBOX).is_file():
        raise RuntimeError('Only the E004 Mac boundary is qualified; no unsandboxed fallback')
    for name in ['tmp', 'config', 'cache', 'state']:
        (run / name).mkdir(exist_ok=True)
    policy = run / 'sandbox.sb'
    policy.write_text(profile(run, binary))
    # Verify syntax before exposing a launcher; this is not the E2E verdict.
    subprocess.run([SANDBOX, '-f', str(policy), '/usr/bin/true'], cwd=run / 'workspace',
                   env=environment(run), check=True, capture_output=True, timeout=15)
    return {'kind': BOUNDARY, 'profile': str(policy), 'sha256': poc.sha256(policy)}


def require(run: Path) -> dict:
    manifest = poc.read_json(run / 'manifest.json')
    boundary = manifest.get('isolation', {})
    policy = run / 'sandbox.sb'
    if (platform.system() != 'Darwin' or boundary.get('kind') != BOUNDARY
            or not policy.is_file() or str(policy) != boundary.get('profile')
            or poc.sha256(policy) != boundary.get('sha256')
            or policy.read_text() != profile(run, manifest['binary'])):
        raise RuntimeError('Fresh E004-qualified isolation required; stale/unprotected runs cannot launch')
    return boundary


def command(run: Path, args: list[str]) -> list[str]:
    require(run)
    return [SANDBOX, '-f', str(run / 'sandbox.sb'), *args]
