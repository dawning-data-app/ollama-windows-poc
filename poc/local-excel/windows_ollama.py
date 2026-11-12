"""Dedicated native Ollama service and resource-admitted model qualification."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
import uuid

import poc
import windows_boundary as boundary
import windows_job as job
import windows_watchdog as watchdog

PORT = 21434
REGISTRY_DIGEST = "56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90"
DIGEST = "5eb3a683cbfed5baef1d1f24e2f54afd93e8a9ba344ca71eb8bb37129cf545fe"
SAMPLER = {"num_ctx": 65536, "temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0,
           "presence_penalty": 0, "repeat_penalty": 1}


def store(manifest):
    # Tool and model stores are siblings in the dedicated evaluator-owned root.
    return Path(manifest["paths"]["opencode_root"]).parent.parent / "models"


def env_for(manifest):
    model_root = store(manifest)
    system_root = Path(os.environ["SystemRoot"])
    return {
        "SystemRoot": str(system_root), "WINDIR": str(system_root),
        "PATH": os.pathsep.join((str(Path(manifest["paths"]["ollama"]).parent), str(system_root / "System32"))),
        "HOME": str(model_root / "runtime-home"), "USERPROFILE": str(model_root / "runtime-home"),
        "LOCALAPPDATA": str(model_root / "runtime-state"),
        "TEMP": str(model_root / "runtime-tmp"), "TMP": str(model_root / "runtime-tmp"),
        "OLLAMA_HOST": f"127.0.0.1:{PORT}", "OLLAMA_MODELS": str(store(manifest)),
        "OLLAMA_NO_CLOUD": "1", "OLLAMA_CONTEXT_LENGTH": str(poc.CONTEXT),
        "OLLAMA_NUM_PARALLEL": "1", "OLLAMA_MAX_LOADED_MODELS": "1", "OLLAMA_KEEP_ALIVE": "10m",
    }


def owner(manifest):
    path = store(manifest) / "guard-owner.json"
    if not path.is_file():
        raise RuntimeError("The dedicated Ollama watchdog has no active ownership receipt")
    value = poc.read_json(path)
    if (value["image"] != manifest["paths"]["ollama"]
            or value["url"] != poc.BASE_URL
            or watchdog.listeners(PORT) != [{"address": "127.0.0.1", "pid": value["pid"]}]
            or job.pid_creation_time(value["pid"]) != value["created_filetime"]):
        raise RuntimeError("Ollama listener does not belong to the dedicated watchdog")
    return value


def stop(manifest, value):
    token = uuid.UUID(hex=value["token"]).hex
    (store(manifest) / (token + ".stop")).touch()


def serve(run, manifest):
    boundary.provisioned(run, manifest)
    models = store(manifest)
    original = models / "manifests/registry.ollama.ai/library/qwen3.5/9b"
    if not original.is_file() or poc.sha256(original) not in (REGISTRY_DIGEST, DIGEST):
        raise RuntimeError("Stage the verified pinned registry model in the dedicated model store")
    overall = datetime.fromisoformat(manifest["overall_deadline"])
    remaining = (overall - datetime.now(timezone.utc)).total_seconds()
    if remaining <= 0 or watchdog.listeners(PORT):
        raise RuntimeError("Dedicated Ollama port is occupied or the overall deadline expired")
    deadline = time.monotonic() + remaining
    for folder in ("runtime-home", "runtime-state", "runtime-tmp"):
        (models / folder).mkdir(exist_ok=True)
    env = env_for(manifest)
    lease = models / "guard-owner.json"
    token = uuid.uuid4().hex
    stop_file = models / (token + ".stop")
    evidence = run / "evidence"
    with lease.open("x", encoding="utf-8") as handle:
        try:
            with ((evidence / "ollama.stdout").open("xb") as stdout,
                  (evidence / "ollama.stderr").open("xb") as stderr, open(os.devnull, "rb") as stdin):
                with job.launch([manifest["paths"]["ollama"], "serve"], models,
                                env, stdio=(stdin, stdout, stderr)) as process:
                    receipt = {
                        **process.identity(), "token": token, "url": poc.BASE_URL,
                        "image": manifest["paths"]["ollama"], "run": run.name, "started": watchdog.timestamp(),
                    }
                    json.dump(receipt, handle)
                    handle.flush()
                    poc.write_json(evidence / "ollama-owner.json", receipt)
                    return watchdog.supervise(process, run, env["SystemRoot"], deadline, port=PORT,
                                              health_path="/api/version", stop_requested=stop_file.exists,
                                              cwd=models)
        finally:
            handle.close()
            lease.unlink()
            stop_file.unlink(missing_ok=True)


def version():
    found = poc.api("/api/version", timeout=5).get("version")
    if found != "0.31.1":
        raise RuntimeError("Dedicated Ollama version differs from 0.31.1")
    return found


def tag_digest():
    tags = poc.api("/api/tags", timeout=5)["models"]
    return next((tag["digest"] for tag in tags if tag["name"] == poc.MODEL), None)


def actual_model():
    loaded = poc.api("/api/ps", timeout=5)["models"]
    if tag_digest() != DIGEST or not any(
            model["name"] == poc.MODEL and model["digest"] == DIGEST
            and model.get("context_length") == poc.CONTEXT for model in loaded):
        raise RuntimeError("Pinned Ollama model digest and exactly 65536 loaded context are required")
    show = poc.api("/api/show", {"model": poc.MODEL}, timeout=5)
    parameters = dict(line.split(maxsplit=1) for line in show["parameters"].splitlines() if line.strip())
    if "tools" not in show.get("capabilities", []) or any(
            key not in parameters or float(parameters[key]) != value for key, value in SAMPLER.items()):
        raise RuntimeError("Pinned Ollama sampler or tool capability differs")
    return {"ollama_version": version(), "models": loaded, "parameters": parameters}


def qualify(run, manifest):
    boundary.require(run, manifest)
    service = owner(manifest)
    env = env_for(manifest)
    deadline = watchdog.case_deadline(datetime.fromisoformat(manifest["overall_deadline"]))
    evidence = run / "evidence"

    def remaining():
        time_left = deadline - time.monotonic()
        if time_left <= 0:
            raise watchdog.GuardStopped("Model qualification deadline reached")
        return time_left

    try:
        version()
        digest = tag_digest()
        if digest == REGISTRY_DIGEST:
            modelfile = evidence / "Modelfile"
            modelfile.write_text(
                f"FROM {poc.MODEL}\n" + "".join(f"PARAMETER {key} {value}\n" for key, value in SAMPLER.items()),
                encoding="ascii", newline="\n",
            )
            build = [manifest["paths"]["ollama"], "create", poc.MODEL, "-f", str(modelfile)]
            if poc.command(build, run, "ollama-create", min(remaining(), 120), env).returncode:
                raise RuntimeError("Ollama Modelfile creation failed")
        if tag_digest() != DIGEST:
            raise RuntimeError("Parameterized model digest differs from Mac baseline")
        watchdog.admit(env["SystemRoot"], run.parent, evidence / "model-admission.jsonl", deadline)
        response = poc.api("/api/chat", {
            "model": poc.MODEL, "stream": False, "think": False, "options": {"num_predict": 64},
            "messages": [{"role": "user", "content": "Call local_probe with value 7. Do not answer in text."}],
            "tools": [{"type": "function", "function": {
                "name": "local_probe", "description": "Local synthetic marker",
                "parameters": {"type": "object", "properties": {"value": {"type": "integer"}},
                               "required": ["value"]},
            }}],
        }, timeout=min(remaining(), 180))
        calls = response.get("message", {}).get("tool_calls", [])
        if not any(call.get("function", {}).get("name") == "local_probe"
                   and call["function"].get("arguments", {}).get("value") == 7 for call in calls):
            raise RuntimeError("Model did not produce the expected tool call")
        poc.api("/v1/chat/completions", {"model": poc.MODEL, "stream": False, "max_tokens": 8,
                "messages": [{"role": "user", "content": "Reply OK."}]}, timeout=min(remaining(), 180))
        remaining()
        result = {"status": "qualified", "guard_token": service["token"], "tool_calls": calls, **actual_model()}
        poc.write_json(evidence / "model-qualification.json", result)
        poc.write_json(store(manifest) / "qualification.json", result)
        return result
    except BaseException:
        stop(manifest, service)
        raise


def require(manifest):
    service = owner(manifest)
    receipt = store(manifest) / "qualification.json"
    if not receipt.is_file():
        raise RuntimeError("Model qualification receipt is missing")
    identity = poc.read_json(receipt)
    if identity.get("status") != "qualified" or identity.get("guard_token") != service["token"]:
        raise RuntimeError("Model qualification belongs to a different Ollama watchdog")
    return service, actual_model()
