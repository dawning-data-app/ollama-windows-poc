"""Dedicated VS Code hosts and evidence capture for existing extensions (Mac).

No extension implementation and no Excel solution are supplied here. GUI input
must be performed in the extension; capture only reads its persisted session.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import socket
import shlex
import subprocess
import poc
import isolation

DIGEST = '5eb3a683cbfed5baef1d1f24e2f54afd93e8a9ba344ca71eb8bb37129cf545fe'
CODE = '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'
EXTENSIONS = {'official': 'sst-dev.opencode@1.0.0', 'chamber': 'fedaykindev.openchamber@1.24.2'}

PROBE = 'POC_CONTEXT_ONLY: synthetic Excel environment; no analysis or expected answers.\n'


def prepare(interface: str, case: str, runs_root: Path, binary: str, probe: bool = False) -> Path:
    binary = str(Path(binary).resolve())
    if not Path(binary).is_file():
        raise ValueError('pinned OpenCode executable is missing')
    run = poc.prepare(runs_root, case)
    env = poc.environment(run)
    qualified = poc.preflight(poc.MODEL)
    if qualified['digest'] != DIGEST:
        raise ValueError('model digest differs from the validated Mac baseline')
    poc.write_json(run / 'evidence/qualification.json', qualified)
    for name, args in [('uv-sync', ['uv', 'sync', '--locked', '--python', '3.12.12']),
                       ('opencode-version', [binary, '--version']),
                       ('python-runtime', ['uv', 'run', '--locked', '--offline', 'python', '-c',
                         "import sys,shutil; print(sys.executable); print(shutil.which('python3'))"]),
                       ('effective-config', [binary, 'debug', 'config'])]:
        result = poc.command(args, run, name, 180, poc.setup_environment() if name == 'uv-sync' else env)
        if result.returncode:
            raise ValueError(f'{name} failed; inspect evidence')
    if (run / 'evidence/opencode-version.stdout').read_text().strip() != '1.19.5':
        raise ValueError('OpenCode upgrade requires a separate decision')
    poc.validate_config(poc.read_json(run / 'evidence/effective-config.stdout'), poc.MODEL)
    (run / 'workspace/context-probe.txt').write_text(PROBE)
    boundary = isolation.prepare(run, binary)
    env = isolation.environment(run)
    poc.write_json(run / 'launch-env.json', env)
    (run / 'bin').mkdir()
    launcher = run / 'bin/opencode'
    python = run / 'workspace/.venv/bin/python'
    launcher.write_text(f'''#!{python}
import json, os, pathlib, sys, time
run = pathlib.Path({str(run)!r})
workspace = run / 'workspace'
policy = run / 'sandbox.sb'
import hashlib
if hashlib.sha256(policy.read_bytes()).hexdigest() != {boundary['sha256']!r}:
    raise SystemExit('Isolation policy changed; refusing launch')
if pathlib.Path.cwd().resolve() != workspace:
    raise SystemExit('Refusing unexpected extension working directory')
env = json.loads((run / 'launch-env.json').read_text())
receipt = {{'cwd': os.getcwd(), 'pid': os.getpid(), 'ppid': os.getppid(),
           'argv': sys.argv[1:], 'python': sys.executable, 'time': time.time(),
           'config': env['OPENCODE_CONFIG'], 'virtual_env': env['VIRTUAL_ENV'],
           'isolation': {boundary!r}}}
with (run / 'evidence/extension-launch.jsonl').open('a') as f:
    f.write(json.dumps(receipt) + '\\n')
os.execve('/usr/bin/sandbox-exec', ['/usr/bin/sandbox-exec', '-f', str(policy), 'uv', 'run', '--locked', '--offline', {binary!r}, *sys.argv[1:]], env)
''')
    launcher.chmod(0o755)
    settings = {'window.title': f'Excel POC {interface} {case} {run.name}',
                'workbench.startupEditor': 'none', 'telemetry.telemetryLevel': 'off',
                'update.mode': 'none', 'extensions.autoUpdate': False,
                'extensions.autoCheckUpdates': False,
                'terminal.integrated.profiles.osx': {'POC zsh': {'path': '/bin/zsh', 'args': ['-f']}},
                'terminal.integrated.defaultProfile.osx': 'POC zsh',
                'terminal.integrated.cwd': str(run / 'workspace'),
                'terminal.integrated.env.osx': {**env, 'PATH': str(run / 'bin') + os.pathsep + env['PATH']}}
    if interface == 'chamber':
        settings['openchamber.opencodeBinary'] = binary
    poc.write_json(run / 'vscode-data/User/settings.json', settings)
    poc.write_json(run / 'session.code-workspace', {'folders': [{'path': str(run / 'workspace')}], 'settings': {k: v for k, v in settings.items() if k not in ('update.mode', 'extensions.autoUpdate', 'extensions.autoCheckUpdates', 'telemetry.telemetryLevel')}})
    manifest = poc.read_json(run / 'manifest.json')
    manifest.update(interface=interface, probe=probe, extension=EXTENSIONS[interface], binary=binary,
                    digest=DIGEST, status='ide-prepared', isolation=boundary, blind_test=isolation.BOUNDARY, context_probe=PROBE,
                    context_probe_sha256=poc.sha256(run / 'workspace/context-probe.txt'))
    poc.write_json(run / 'manifest.json', manifest)
    return run


def start_server(run: Path) -> None:
    """OpenChamber's supported external-API mode; never upgrade its backend."""
    isolation.require(run)
    manifest = poc.read_json(run / 'manifest.json')
    if manifest['interface'] != 'chamber' or (run / 'server.json').exists():
        raise ValueError('server already prepared or wrong interface')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    log = (run / 'evidence/server.log').open('w')
    proc = subprocess.Popen(isolation.command(run, ['uv', 'run', '--locked', '--offline', manifest['binary'], 'serve', '--hostname', '127.0.0.1', '--port', str(port)]),
                            cwd=run / 'workspace', env=isolation.environment(run), stdout=log, stderr=log,
                            start_new_session=True)
    log.close()
    endpoint = f'http://127.0.0.1:{port}'
    poc.write_json(run / 'server.json', {'pid': proc.pid, 'url': endpoint, 'cwd': str(run / 'workspace'), 'isolation': manifest['isolation']})
    settings_path = run / 'vscode-data/User/settings.json'
    settings = poc.read_json(settings_path)
    settings['openchamber.apiUrl'] = endpoint
    poc.write_json(settings_path, settings)
    poc.write_json(run / 'session.code-workspace', {'folders': [{'path': str(run / 'workspace')}], 'settings': {k: v for k, v in settings.items() if k not in ('update.mode', 'extensions.autoUpdate', 'extensions.autoCheckUpdates', 'telemetry.telemetryLevel')}})
    print(endpoint)


def launch(run: Path) -> None:
    isolation.require(run)
    manifest = poc.read_json(run / 'manifest.json')
    if manifest['status'] != 'ide-prepared':
        raise ValueError('launch requires a fresh prepared IDE run')
    if manifest['interface'] == 'chamber' and not (run / 'server.json').is_file():
        raise ValueError('start the controlled local API first')
    env = poc.environment(run)
    env['PATH'] = str(run / 'bin') + os.pathsep + env['PATH']
    log = (run / 'evidence/vscode.log').open('w')
    profile = 'Excel POC Official' if manifest['interface'] == 'official' else 'Excel POC OpenChamber'
    versions = subprocess.run([CODE, '--profile', profile, '--list-extensions', '--show-versions'],
                              capture_output=True, text=True, timeout=30, check=True)
    (run / 'evidence/vscode-extension-versions.stdout').write_text(versions.stdout)
    if EXTENSIONS[manifest['interface']] not in versions.stdout.splitlines():
        log.close()
        raise ValueError('Create the dedicated VS Code profile and install its pinned extension first')
    p = subprocess.Popen([CODE, '--new-window', '--profile', profile, str(run / 'session.code-workspace')],
                         cwd=run / 'workspace', env=env, stdout=log, stderr=log, start_new_session=True)
    log.close()
    manifest.update(status='ide-launched-needs-review', vscode_launcher_pid=p.pid, vscode_profile=profile)
    poc.write_json(run / 'manifest.json', manifest)


def ran_analysis_python(part: dict) -> bool:
    state = part.get('state', {})
    if part.get('tool') != 'bash' or state.get('status') != 'completed' or state.get('metadata', {}).get('exit') != 0:
        return False
    try:
        args = shlex.split(state.get('input', {}).get('command', ''))
    except ValueError:
        return False
    prefix = ['uv', 'run', '--locked', '--offline', 'python']
    return any((i == 0 or args[i - 1] in ('&&', ';')) and args[i:i + 5] == prefix
               and Path(args[i + 5]).name == 'analysis.py' for i in range(max(0, len(args) - 5)))


def capture(run: Path, session_id: str | None) -> dict:
    manifest = poc.read_json(run / 'manifest.json')
    binary = manifest['binary']
    env = poc.environment(run)
    if session_id is None:
        result = subprocess.run([binary, 'session', 'list', '--format', 'json'], cwd=run / 'workspace',
                                env=env, capture_output=True, text=True, check=True)
        poc.write_json(run / 'evidence/session-list.json', json.loads(result.stdout))
        return {'sessions': json.loads(result.stdout)}
    result = subprocess.run([binary, 'export', session_id], cwd=run / 'workspace', env=env,
                            capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    poc.write_json(run / 'evidence/session-export.json', data)
    loaded = poc.api('/api/ps')
    poc.write_json(run / 'evidence/loaded-after.json', loaded)
    errors = []
    if manifest.get('isolation'):
        try:
            boundary = isolation.require(run)
            if manifest['interface'] == 'official':
                receipts = [json.loads(line) for line in (run / 'evidence/extension-launch.jsonl').read_text().splitlines()]
            else:
                receipts = [poc.read_json(run / 'server.json')]
            if not receipts or any(r.get('isolation') != boundary or r.get('cwd') != str(run / 'workspace') for r in receipts):
                errors.append('execution boundary receipt differs from prepared session')
        except (OSError, ValueError, RuntimeError, KeyError):
            errors.append('execution boundary not confirmed')
    workspace = run / 'workspace'
    for name, key in [('uv.lock', 'lock_sha256'), ('opencode.json', 'config_sha256'),
                      ('context-probe.txt', 'context_probe_sha256')]:
        if not (workspace / name).is_file() or poc.sha256(workspace / name) != manifest[key]:
            errors.append('protected input changed: ' + name)
    fixture = workspace / '銷售 資料/sales.xlsx'
    if manifest['case'] != 'missing' and (not fixture.is_file() or poc.sha256(fixture) != manifest['fixture_sha256']):
        errors.append('fixture changed')
    messages = data['messages']
    assistants = [m for m in messages if m['info']['role'] == 'assistant']
    if not assistants or assistants[-1]['info'].get('finish') != 'stop':
        errors.append('final assistant response is incomplete')
    models = {(m['info'].get('providerID'), m['info'].get('modelID')) for m in assistants}
    if models != {('ollama', poc.MODEL)}:
        errors.append('unexpected assistant inference route')
    parts = [p for m in messages for p in m['parts']]
    tools = [p for p in parts if p['type'] == 'tool']
    final = '\n'.join(p.get('text', '') for p in assistants[-1]['parts'] if p['type'] == 'text') if assistants else ''
    if manifest.get('probe'):
        if not any(p.get('tool') == 'bash' and p.get('state', {}).get('metadata', {}).get('exit') == 0
                   and str(workspace / '.venv') in p.get('state', {}).get('output', '') for p in tools):
            errors.append('no real session Python environment probe')
        if not final.strip():
            errors.append('no final probe response')
    elif manifest['case'] == 'sales':
        try:
            errors.extend(poc.compare_answer(poc.read_json(workspace / 'answer.json'), poc.read_json(poc.ROOT / 'oracle.json')))
        except (OSError, ValueError):
            errors.append('missing or invalid answer.json')
        if not (workspace / 'analysis.py').is_file() or not any(ran_analysis_python(p) for p in tools):
            errors.append('no successful generated Python execution')
        if '12000' not in final.replace(',', ''):
            errors.append('final numeric conversation missing')
    else:
        if (workspace / 'answer.json').exists():
            errors.append('negative case produced an answer file')
        if not tools or not final.strip():
            errors.append('missing negative discovery or explanation')
        if manifest['case'] == 'missing' and fixture.parent.exists():
            errors.append('agent created missing input folder')
    if not any(m['name'] == poc.MODEL and m['digest'] == DIGEST and m.get('context_length', 0) >= poc.CONTEXT for m in loaded['models']):
        errors.append('loaded model digest/context not confirmed')
    inference_log = run / 'state/opencode/log/opencode.log'
    log_text = inference_log.read_text() if inference_log.exists() else ''
    (run / 'evidence/inference.log').write_text(log_text)
    streams = [line for line in log_text.splitlines() if 'message=stream' in line and session_id in line]
    if not all(any(f'small={size}' in line and f'modelID={poc.MODEL}' in line
                   and 'providerID=ollama' in line for line in streams) for size in ('true', 'false')):
        errors.append('main/small inference identities not both observed')
    user_parts = [p for m in messages if m['info']['role'] == 'user' for p in m['parts']]
    poc.write_json(run / 'evidence/submitted-context.json', user_parts)
    report = {'status': 'needs-human-review' if not errors else 'not-passed', 'errors': errors,
              'interface': manifest['interface'], 'case': manifest['case'], 'session_id': session_id,
              'models': sorted(models), 'e2e_passed': False,
              'manual_checks': ['actual extension GUI submission and tool/final rendering',
                                'source really reads/calculates XLSX; no oracle contamination',
                                'extra file/selection context and actual launch environment',
                                'negative-case narrative and all numeric/group/rank relations']}
    poc.write_json(run / 'interface-review.json', report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--interface', choices=['official', 'chamber'], required=True)
    prep.add_argument('--probe', action='store_true')
    prep.add_argument('--case', choices=['sales', 'missing', 'corrupt'], default='sales')
    prep.add_argument('--runs-root', type=Path, required=True)
    prep.add_argument('--opencode', required=True)
    for action in ['launch', 'server', 'capture']:
        command = sub.add_parser(action)
        command.add_argument('run', type=Path)
        if action == 'capture':
            command.add_argument('--session-id')
    args = parser.parse_args()
    if args.action == 'prepare':
        print(prepare(args.interface, args.case, args.runs_root, args.opencode, args.probe))
    elif args.action == 'launch':
        launch(args.run.resolve())
    elif args.action == 'server':
        start_server(args.run.resolve())
    else:
        print(json.dumps(capture(args.run.resolve(), args.session_id), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
