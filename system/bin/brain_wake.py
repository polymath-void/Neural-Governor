#!/usr/bin/env python3
import sys, json, time
import urllib.request
import subprocess

CONFIG_FILE = "/data/adb/modules/resource-orchestrator/system/etc/resource_config.sh"
SNAPSHOT_FILE = "/data/local/tmp/neural_snapshot.json"
LOG_FILE = "/data/local/tmp/neural_execution_history.jsonl"
ACTION_FILE = "/data/local/tmp/neural_action.txt"

def get_api_key():
    try:
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                if line.startswith("export GEMINI_API_KEY="):
                    return line.split("=")[1].strip().strip('"')
    except Exception:
        pass
    return None

def read_snapshot():
    try:
        with open(SNAPSHOT_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def append_log(snap_before, user_prompt, response, command, exec_log):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "snapshot_before": snap_before,
        "user_prompt": user_prompt,
        "brain_response": response,
        "executed_command": command,
        "execution_log": exec_log
    }
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        subprocess.run(["chmod", "666", LOG_FILE], stderr=subprocess.DEVNULL)
    except Exception:
        pass

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
        
    trigger_reason = sys.argv[1]
    is_manual = trigger_reason.startswith("MANUAL:")
    
    api_key = get_api_key()
    if not api_key:
        sys.exit(1)

    # Use gemini-3.1-flash-lite (falling back to gemini-2.5-flash if 3.1 is not available on this endpoint)
    # The URL defaults to gemini-2.5-flash for compatibility with AI studio free tier if 3.1-flash-lite isn't released globally, 
    # but we will try 2.5 flash if 3.1 fails, or just use 3.1-flash-lite directly if requested.
    # The prompt explicitly asked for gemini-3.1-flash-lite. We'll set it, but we can fallback if it fails.
    model = "gemini-2.5-flash" # Temporary safe fallback, adjust if 3.1-flash-lite is definitely live
    # We will try gemini-2.5-flash for now since 3.1-flash-lite might throw 404 on some API keys.
    # Wait, the user specifically asked for gemini-3.1-flash-lite. Let's use it.
def ask_brain(api_key, model, trigger_reason, snap, error_context=None, prev_cmd=None):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt = f"""You are Neural-Governor Brain.
Trigger: {trigger_reason}
System Snapshot: {json.dumps(snap)}

RULES:
1. Reason about the trigger. If it's a thermal spike, high CPU, or battery drain, you MUST output a bash command to mitigate it (e.g. renice, kill, drop_caches).
2. If it's a manual user request, answer it or provide the command.
3. You must format your response exactly like this:
EXPLANATION: <briefly explain the issue and solution>
COMMAND: <exact bash command to run, or NONE>
"""
    if error_context:
        prompt += f"\n\n[URGENT FALLBACK REQUIRED]\nYour previous command `{prev_cmd}` failed to execute.\nError Output:\n{error_context}\nPlease analyze why it failed and provide a DIFFERENT, safer alternative COMMAND."

    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode("utf-8"))
            action_text = res["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            explanation = ""
            command = ""
            for line in action_text.split('\n'):
                if line.startswith("EXPLANATION:"):
                    explanation = line.replace("EXPLANATION:", "").strip()
                elif line.startswith("COMMAND:"):
                    command = line.replace("COMMAND:", "").strip()
            if not command and not explanation:
                explanation = action_text
            return explanation, command
    except Exception as e:
        return f"API Error: {str(e)}", ""

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
        
    trigger_reason = sys.argv[1]
    is_manual = trigger_reason.startswith("MANUAL:")
    
    api_key = get_api_key()
    if not api_key:
        sys.exit(1)

    model = "gemini-3.1-flash-lite"
    snap = read_snapshot()
    
    explanation, command = ask_brain(api_key, model, trigger_reason, snap)
    
    exec_log = ""
    if command and command != "NONE":
        try:
            proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            exec_log = proc.stdout + "\n" + proc.stderr
            
            # FALLBACK MECHANISM: If the command failed, ask the AI for a different method
            if proc.returncode != 0 and not is_manual:
                exec_log = f"Failed (Exit {proc.returncode}): {proc.stderr.strip()}"
                
                exp2, cmd2 = ask_brain(api_key, model, trigger_reason, snap, exec_log, command)
                explanation += f"\n[FALLBACK TRIGGERED] Original failed. New Reasoning: {exp2}"
                command = cmd2
                
                if cmd2 and cmd2 != "NONE":
                    proc2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True, timeout=10)
                    exec_log += f"\n[Fallback Output] {proc2.stdout} \n {proc2.stderr}"

            with open(ACTION_FILE, "w") as f:
                f.write(command)
            subprocess.run(["chmod", "666", ACTION_FILE], stderr=subprocess.DEVNULL)
        except Exception as e:
            exec_log = f"Exception: {str(e)}"
            
    if not is_manual:
        append_log(snap, trigger_reason, explanation, command, exec_log.strip())
    else:
        print(f"EXPLANATION: {explanation}")
        print(f"COMMAND: {command}")
        print(f"OUTPUT: {exec_log.strip()}")

if __name__ == "__main__":
    main()
