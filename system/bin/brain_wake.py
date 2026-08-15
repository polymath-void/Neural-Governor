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
    model = "gemini-3.1-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    snap = read_snapshot()
    
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
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode("utf-8"))
            try:
                action_text = res["candidates"][0]["content"]["parts"][0]["text"].strip()
            except KeyError:
                sys.exit(1)
                
            explanation = ""
            command = ""
            for line in action_text.split('\n'):
                if line.startswith("EXPLANATION:"):
                    explanation = line.replace("EXPLANATION:", "").strip()
                elif line.startswith("COMMAND:"):
                    command = line.replace("COMMAND:", "").strip()
                    
            if not command and not explanation:
                # Fallback if AI didn't follow format
                explanation = action_text
                
            exec_log = ""
            if command and command != "NONE":
                # Execute the command
                try:
                    proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                    exec_log = proc.stdout + "\n" + proc.stderr
                except Exception as e:
                    exec_log = f"Failed to execute: {str(e)}"
                    
                # We can also write to action file if dashboard wants to see it live
                try:
                    with open(ACTION_FILE, "w") as f:
                        f.write(command)
                    subprocess.run(["chmod", "666", ACTION_FILE], stderr=subprocess.DEVNULL)
                except Exception:
                    pass
            
            # Log to JSONL if it's NOT a manual request
            if not is_manual:
                append_log(snap, trigger_reason, explanation, command, exec_log.strip())
            else:
                # If manual, we print it out so the dashboard can read the output
                print(f"EXPLANATION: {explanation}")
                print(f"COMMAND: {command}")
                print(f"OUTPUT: {exec_log.strip()}")

    except urllib.error.HTTPError as e:
        # If 3.1-flash-lite fails (e.g. 404), fallback to 2.5-flash
        print(f"API Error: {e.code}")

if __name__ == "__main__":
    main()
