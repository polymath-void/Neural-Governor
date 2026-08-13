#!/usr/bin/env python3
import json
import time
import urllib.request
import urllib.error
import os
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
    except Exception as e:
        pass

def run_brain(snapshot, custom_prompt=None):
    api_key = get_api_key()
    if not api_key:
        return "Error: API Key missing."
        
    model = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt = "You are Neural-Governor. Analyze this system state and output exactly ONE short shell command to optimize resource usage (or 'echo stable' if fine):\n"
    prompt += json.dumps(snapshot)
    if custom_prompt:
        prompt = f"User Request: {custom_prompt}\nContext: {json.dumps(snapshot)}\nOutput exactly ONE shell command to achieve the request."

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
                return f"API Error: Reached token limit or missing parts. Raw: {res.get('candidates', [{}])[0].get('finishReason', 'Unknown')}"
            
            # Clean up markdown if any
            if action.startswith("```"):
                action = action.split("\n")[1]
            elif action.startswith("`"):
                action = action.strip("`")
            write_action(action)
            return action
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
        Layout(name="sys_metrics", ratio=1),
        Layout(name="brain_output", ratio=2)
    )
    
    metrics_panel = Panel(Text(sys_info, style="green"), title="[ Hardware Context Snapshot ]", border_style="green")
    layout["sys_metrics"].update(metrics_panel)
    
    brain_panel = Panel(Text(brain_output, style="yellow"), title="[ Brain Processing & Action ]", border_style="yellow")
    layout["main"]["brain_output"].update(brain_panel)
    
    footer = Panel(Text("Type a custom prompt for the brain, or press Enter for autonomous action. (Type 'exit' to stop)", style="dim white"), border_style="blue")
    layout["footer"].update(footer)
    
    return layout

def main():
    check_api_key()
    console.clear()
    
    initial_output = "Connecting to Gemini AI Studio..."
    sys_info = "Waiting for daemon snapshot..."
    
    with Live(generate_layout(initial_output, sys_info), refresh_per_second=4, screen=True) as live:
        time.sleep(1)
        snap = read_snapshot()
        if snap:
            sys_info = f"CPU: {snap.get('cpu_stat', '')[:30]}...\n{snap.get('mem_info', '')}\nBattery: {snap.get('battery')}%\nThermal: {snap.get('thermal')}"
            initial_output = f"Action Issued: {run_brain(snap)}"
        else:
            initial_output = "Error: Daemon snapshot not found. Is resource-orchestrator running?"
        live.update(generate_layout(initial_output, sys_info))
    
    while True:
        console.clear()
        console.print(generate_layout(initial_output, sys_info))
        user_input = Prompt.ask("\n[bold cyan]Prompt[/bold cyan]")
        
        if user_input.lower() in ['exit', 'quit']:
            break
            
        snap = read_snapshot()
        sys_info = f"CPU: {snap.get('cpu_stat', '')[:30]}...\n{snap.get('mem_info', '')}\nBattery: {snap.get('battery')}%\nThermal: {snap.get('thermal')}" if snap else "Error reading snapshot"
        
        console.clear()
        with Live(generate_layout("Brain is consulting Gemini API...", sys_info), refresh_per_second=4, screen=True) as live:
            initial_output = f"Action Issued: {run_brain(snap, user_input)}"
            live.update(generate_layout(initial_output, sys_info))

if __name__ == "__main__":
    main()
