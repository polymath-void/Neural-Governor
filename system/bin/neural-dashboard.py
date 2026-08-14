#!/usr/bin/env python3
import json
import time
import urllib.request
import urllib.error
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt
from rich.align import Align

console = Console()
CONFIG_FILE = "/data/adb/modules/resource-orchestrator/system/etc/resource_config.sh"
SNAPSHOT_FILE = "/data/local/tmp/neural_snapshot.json"
ACTION_FILE = "/data/local/tmp/neural_action.txt"
LOG_FILE = "/data/local/tmp/neural_execution_history.jsonl"

# State variables
command_history = []
current_mode = "Auto (AI Controlled)"
AVAILABLE_MODES = ["Auto (AI Controlled)", "Performance", "BatterySaver", "Balanced"]

def get_api_key():
    try:
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                if line.startswith("export GEMINI_API_KEY="):
                    return line.split("=")[1].strip().strip('"')
    except Exception:
        pass
    return None

def check_api_key():
    if not get_api_key() or get_api_key() == "YOUR_KEY_HERE":
        console.clear()
        console.print(Panel(Align.center(Text("API Key Configuration Required", style="bold yellow"))))
        api_key = Prompt.ask("\n[bold cyan]Please paste your Google AI Studio Gemini API Key[/bold cyan]")
        if api_key:
            new_content = f'export GEMINI_API_KEY="{api_key}"\n'
            subprocess.run(["su", "-c", f"echo '{new_content}' > {CONFIG_FILE}"])
            console.print("\n[bold green]API Key saved successfully![/bold green]")
            time.sleep(1)

def read_snapshot():
    try:
        with open(SNAPSHOT_FILE, "r") as f:
            data = json.load(f)
            return data
    except Exception:
        return None

def write_action(command):
    try:
        subprocess.run(["su", "-c", f"echo '{command}' > {ACTION_FILE}"])
        command_history.append(f"> {command}")
        if len(command_history) > 10:
            command_history.pop(0)
    except Exception as e:
        pass

def append_log(snap_before, user_prompt, response, command, snap_after):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "snapshot_before": snap_before,
        "user_prompt": user_prompt,
        "brain_response": response,
        "executed_command": command,
        "snapshot_after": snap_after
    }
    try:
        # Save to local termux directory instead of root temp if possible, but sticking to /data/local/tmp for cross-process
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        # Ensure it is readable
        subprocess.run(["su", "-c", f"chmod 666 {LOG_FILE}"], stderr=subprocess.DEVNULL)
    except Exception:
        pass

def run_brain(snapshot, custom_prompt=None, mode="Auto"):
    api_key = get_api_key()
    if not api_key:
        return "Error: API Key missing."
        
    model = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt = f"""You are Neural-Governor, an AI kernel orchestrator for Android.
Current Operating Mode: {mode}
System Snapshot: {json.dumps(snapshot)}

CRITICAL RULES:
1. ONLY output safe performance, battery saving, thermal, paging, or renice commands. Do NOT run dangerous commands (e.g. rm, dd).
2. If the user makes an individual request, asks a question, or requests something unsafe, you MUST discuss it with them by outputting normal text prefixed with "CHAT: ".
3. If the system is stable and no command is needed, output: CHAT: System stable.
4. If an action is required, output EXACTLY ONE shell command and nothing else.

User Prompt (if any): {custom_prompt if custom_prompt else "Autonomous monitoring cycle."}
"""

    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500}
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode("utf-8"))
            try:
                action = res["candidates"][0]["content"]["parts"][0]["text"].strip()
            except KeyError:
                return f"API Error: Reached token limit or missing parts."
            
            if action.startswith("```"):
                action = action.split("\n")[1]
                
            if action.startswith("CHAT:"):
                chat_msg = action.replace("CHAT:", "").strip()
                append_log(snapshot, custom_prompt, chat_msg, None, None)
                return f"[AI Discussion]\n{chat_msg}"
            else:
                write_action(action)
                # Pause to let the daemon execute and the system stabilize
                time.sleep(2)
                snap_after = read_snapshot()
                append_log(snapshot, custom_prompt, action, action, snap_after)
                return f"[Action Executed]\n{action}"
    except Exception as e:
        return f"API Error: {e}"

def generate_layout(brain_output, sys_info):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    header = Panel(Align.center(Text("🧠 NEURAL GOVERNOR AI STUDIO 🧠", style="bold cyan")), style="cyan")
    layout["header"].update(header)
    
    layout["main"].split_row(
        Layout(name="left_panel", ratio=1),
        Layout(name="brain_output", ratio=2)
    )
    
    layout["left_panel"].split_column(
        Layout(name="sys_metrics", ratio=1),
        Layout(name="cmd_log", ratio=1)
    )
    
    metrics_panel = Panel(Text(sys_info, style="green"), title="[ Hardware Context Snapshot ]", border_style="green")
    layout["sys_metrics"].update(metrics_panel)
    
    log_text = "\n".join(command_history) if command_history else "No commands executed yet."
    log_panel = Panel(Text(log_text, style="magenta"), title="[ Executed Command Log ]", border_style="magenta")
    layout["cmd_log"].update(log_panel)
    
    brain_panel = Panel(Text(brain_output, style="yellow"), title="[ Brain Processing & Action ]", border_style="yellow")
    layout["main"]["brain_output"].update(brain_panel)
    
    footer = Panel(Text("Type '/mode [num]' to change modes. Press Enter to poll AI. Type text to discuss with AI. (Type 'exit' to stop)", style="dim white"), border_style="blue")
    layout["footer"].update(footer)
    
    return layout

def format_sys_info(snap, mode):
    if not snap:
        return "Waiting for daemon snapshot..."
    return f"Mode: {mode}\nCPU: {snap.get('cpu_stat', '')[:30]}...\n{snap.get('mem_info', '')}\nBattery: {snap.get('battery')}%\nThermal: {snap.get('thermal')}"

def main():
    global current_mode
    check_api_key()
    console.clear()
    
    initial_output = "Connecting to Gemini AI Studio..."
    sys_info = format_sys_info(read_snapshot(), current_mode)
    
    with Live(generate_layout(initial_output, sys_info), refresh_per_second=4, screen=True) as live:
        time.sleep(1)
        snap = read_snapshot()
        if snap:
            sys_info = format_sys_info(snap, current_mode)
            initial_output = run_brain(snap, None, current_mode)
        else:
            initial_output = "Error: Daemon snapshot not found. Is resource-orchestrator running?"
        live.update(generate_layout(initial_output, sys_info))
    
    while True:
        console.clear()
        console.print(generate_layout(initial_output, sys_info))
        user_input = Prompt.ask("\n[bold cyan]Prompt[/bold cyan]")
        
        if user_input.lower() in ['exit', 'quit']:
            console.clear()
            console.print("[bold green]Exiting Neural Governor Dashboard...[/bold green]")
            import os
            os.system('stty sane')
            break
            
        if user_input.lower().startswith("/mode"):
            try:
                print("Modes: 1. Auto 2. Performance 3. BatterySaver 4. Balanced")
                m = Prompt.ask("Select mode (1-4)")
                idx = int(m) - 1
                if 0 <= idx < len(AVAILABLE_MODES):
                    current_mode = AVAILABLE_MODES[idx]
                    initial_output = f"[AI Discussion]\nMode switched to {current_mode}."
                else:
                    initial_output = "[AI Discussion]\nInvalid mode selected."
            except ValueError:
                initial_output = "[AI Discussion]\nInvalid input."
            
            snap = read_snapshot()
            sys_info = format_sys_info(snap, current_mode)
            continue
            
        snap = read_snapshot()
        sys_info = format_sys_info(snap, current_mode)
        
        console.clear()
        with Live(generate_layout("Brain is consulting Gemini API...", sys_info), refresh_per_second=4, screen=True) as live:
            initial_output = run_brain(snap, user_input if user_input else None, current_mode)
            live.update(generate_layout(initial_output, sys_info))

if __name__ == "__main__":
    main()
