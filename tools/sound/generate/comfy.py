"""ComfyUI access for the generated sounds: the same install, models and workflows the Genesis project used
(D:\\genesis-vr\\tools\\make_audio.py): ACE-Step 1.5 turbo for music, Stable Audio Open 1.0 for effects and ambience.

    python comfy.py start     # start ComfyUI if nothing answers on 8188; remembers the pid only when WE started it
    python comfy.py stop      # stop it, only if we started it
    python comfy.py status

Nothing is substituted: if the install or a model file is missing, check() says exactly which one and everything stops.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

COMFY = r"D:\godtree-tools\ComfyUI_windows_portable"
EXTRA = r"D:\godtree-tools\extra_model_paths.yaml"
MODELS = r"D:\godtree-tools\models"
SERVER = "http://127.0.0.1:8188"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CAND = os.path.join(ROOT, "work", "sound_candidates")
PIDFILE = os.path.join(CAND, "comfy_started_by_us.json")

NEEDED = [os.path.join(COMFY, "python_embeded", "python.exe"), os.path.join(COMFY, "ComfyUI", "main.py"), EXTRA,
          os.path.join(MODELS, "checkpoints", "ace_step_1.5_turbo_aio.safetensors"),
          os.path.join(MODELS, "checkpoints", "stable-audio-open-1.0.safetensors"),
          os.path.join(MODELS, "text_encoders", "t5_base.safetensors")]

# Workflows copied from the Genesis project (only the prompt text, seed, bpm, key and lengths are changed per sound)
ACE = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ace_step_1.5_turbo_aio.safetensors"}},
       "2": {"class_type": "TextEncodeAceStepAudio1.5", "inputs": {
           "clip": ["1", 1], "tags": "", "lyrics": "[Instrumental]", "seed": 0, "bpm": 60, "duration": 30.0,
           "timesignature": "4", "language": "en", "keyscale": "C major", "generate_audio_codes": True,
           "cfg_scale": 2.0, "temperature": 0.85, "top_p": 0.9, "top_k": 0, "min_p": 0.0}},
       "3": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["2", 0]}},
       "4": {"class_type": "EmptyAceStep1.5LatentAudio", "inputs": {"seconds": 30.0, "batch_size": 1}},
       "5": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
       "6": {"class_type": "KSampler", "inputs": {"model": ["5", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0],
                                                  "seed": 0, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
       "7": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
       "8": {"class_type": "SaveAudio", "inputs": {"audio": ["7", 0], "filename_prefix": "angel"}}}
SAO = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "stable-audio-open-1.0.safetensors"}},
       "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5_base.safetensors", "type": "stable_audio", "device": "default"}},
       "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": ""}},
       "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": "music, melody, speech, voice, low quality, hiss, noise, distortion"}},
       "5": {"class_type": "ConditioningStableAudio", "inputs": {"positive": ["3", 0], "negative": ["4", 0], "seconds_start": 0.0, "seconds_total": 10.0}},
       "6": {"class_type": "EmptyLatentAudio", "inputs": {"seconds": 10.0, "batch_size": 1}},
       "7": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["5", 0], "negative": ["5", 1], "latent_image": ["6", 0],
                                                  "seed": 0, "steps": 60, "cfg": 6.0, "sampler_name": "dpmpp_3m_sde_gpu", "scheduler": "exponential", "denoise": 1.0}},
       "8": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
       "9": {"class_type": "SaveAudio", "inputs": {"audio": ["8", 0], "filename_prefix": "angel"}}}


def check():
    missing = [p for p in NEEDED if not os.path.exists(p)]
    if missing:
        sys.exit("MISSING, nothing will be substituted:\n  " + "\n  ".join(missing))


def api(path, body=None, timeout=60):
    req = urllib.request.Request(SERVER + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def up():
    try:
        api("/system_stats", timeout=5)
        return True
    except Exception:
        return False


def start():
    """start ComfyUI unless one already answers; returns True if we started it"""
    check()
    if up():
        print("ComfyUI already running (not ours: left alone)")
        return False
    os.makedirs(CAND, exist_ok=True)
    log = open(os.path.join(CAND, "comfy.log"), "w")
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.Popen([os.path.join(COMFY, "python_embeded", "python.exe"), "-s", r"ComfyUI\main.py", "--windows-standalone-build",
                             "--disable-auto-launch", "--listen", "127.0.0.1", "--port", "8188", "--extra-model-paths-config", EXTRA],
                            cwd=COMFY, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
    json.dump({"pid": proc.pid, "started": time.strftime("%Y-%m-%d %H:%M:%S")}, open(PIDFILE, "w"))
    for _ in range(150):
        time.sleep(2)
        if up():
            print("ComfyUI up, pid", proc.pid)
            return True
        if proc.poll() is not None:
            sys.exit("ComfyUI stopped while starting; see " + os.path.join(CAND, "comfy.log"))
    sys.exit("ComfyUI did not come up")


def stop():
    if not os.path.exists(PIDFILE):
        print("no ComfyUI of ours to stop")
        return
    pid = json.load(open(PIDFILE))["pid"]
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    os.remove(PIDFILE)
    time.sleep(2)
    print("stopped pid", pid, "| still answering:", up())


def run(workflow, prefix, timeout=900):
    """queue a workflow, wait for it, return the path of the saved flac"""
    saver = next(n for n in workflow.values() if n["class_type"] == "SaveAudio")
    saver["inputs"]["filename_prefix"] = "angel/" + prefix
    pid = api("/prompt", {"prompt": workflow})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(1)
        hist = api(f"/history/{pid}")
        if pid in hist:
            status = hist[pid].get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(json.dumps(status)[:800])
            for out in hist[pid].get("outputs", {}).values():
                for a in out.get("audio", []):
                    return os.path.join(COMFY, "ComfyUI", "output", a.get("subfolder", ""), a["filename"])
    raise TimeoutError(prefix)


def ace(tags, seconds, seed, bpm, key, lyrics="[Instrumental]", timesig="4", prefix="ace"):
    wf = json.loads(json.dumps(ACE))
    wf["2"]["inputs"].update({"tags": tags, "bpm": int(bpm), "keyscale": key, "duration": float(seconds), "seed": int(seed),
                              "lyrics": lyrics, "timesignature": timesig})
    wf["4"]["inputs"]["seconds"] = float(seconds)
    wf["6"]["inputs"]["seed"] = int(seed)
    return run(wf, prefix)


def sao(prompt, seconds, seed, negative=None, prefix="sao", steps=60, cfg=6.0):
    wf = json.loads(json.dumps(SAO))
    wf["3"]["inputs"]["text"] = prompt
    if negative is not None:
        wf["4"]["inputs"]["text"] = negative
    wf["5"]["inputs"]["seconds_total"] = float(seconds)
    wf["6"]["inputs"]["seconds"] = float(seconds)
    wf["7"]["inputs"].update({"seed": int(seed), "steps": steps, "cfg": cfg})
    return run(wf, prefix)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    else:
        check()
        print("all files present; ComfyUI answering:", up())
