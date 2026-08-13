#!/usr/bin/env python3
import subprocess
import time
import sys
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt
from rich.align import Align

console = Console()
GOVERNOR_BIN = "/data/data/com.termux/files/home/Projects/Neural-Governor/system/bin/resource-orchestrator"

def get_sys_info():
    try:
        with open("/proc/stat", "r") as f:
            cpu = f.readline().strip()
        with open("/proc/meminfo", "r") as f:
            mem = [f.readline().strip() for _ in range(2)]
        return f"CPU: {cpu[:30]}...\n{mem[0]}\n{mem[1]}"
    except:
        return "System metrics unavailable"

def run_brain(prompt=None):
    cmd = [GOVERNOR_BIN]
    if prompt:
        cmd.append(prompt)
    try:
        # Run binary and capture output
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return res.stdout if res.returncode == 0 else f"Error: {res.stderr}"
    except Exception as e:
        return f"Failed to execute brain: {e}"

def generate_layout(brain_output, sys_info):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    header = Panel(Align.center(Text("🧠 POLYMATH-VOID NEURAL GOVERNOR 🧠", style="bold cyan")), style="cyan")
    layout["header"].update(header)
    
    layout["main"].split_row(
        Layout(name="sys_metrics", ratio=1),
        Layout(name="brain_output", ratio=2)
    )
    
    metrics_panel = Panel(Text(sys_info, style="green"), title="[ Hardware Context ]", border_style="green")
    layout["sys_metrics"].update(metrics_panel)
    
    brain_panel = Panel(Text(brain_output, style="yellow"), title="[ Brain Processing & Action ]", border_style="yellow")
    layout["main"]["brain_output"].update(brain_panel)
    
    footer = Panel(Text("Type a custom prompt for the brain, or press Enter for autonomous action. (Type 'exit' to stop)", style="dim white"), border_style="blue")
    layout["footer"].update(footer)
    
    return layout

CONFIG_FILE = "/data/adb/modules/resource-orchestrator/system/etc/resource_config.sh"

def check_api_key():
    try:
        with open(CONFIG_FILE, "r") as f:
            content = f.read()
    except Exception:
        content = ""
    
    if "YOUR_KEY_HERE" in content or "GEMINI_API_KEY" not in content:
        console.clear()
        console.print(Panel(Align.center(Text("API Key Configuration Required", style="bold yellow"))))
        api_key = Prompt.ask("\n[bold cyan]Please paste your Gemini API Key[/bold cyan]")
        if api_key:
            new_content = f'export GEMINI_API_KEY="{api_key}"\n'
            # Write to the secure Magisk location using su
            subprocess.run(["su", "-c", f"echo '{new_content}' > {CONFIG_FILE}"])
            console.print("\n[bold green]API Key saved successfully![/bold green]")
            time.sleep(1)

def main():
    check_api_key()
    console.clear()
    
    # Initial autonomous run
    initial_output = "Booting Neural-Governor...\nAnalyzing context..."
    sys_info = get_sys_info()
    
    with Live(generate_layout(initial_output, sys_info), refresh_per_second=4, screen=True) as live:
        time.sleep(1)
        initial_output = run_brain()
        live.update(generate_layout(initial_output, sys_info))
    
    # Interactive loop
    while True:
        console.clear()
        console.print(generate_layout(initial_output, sys_info))
        
        user_input = Prompt.ask("\n[bold cyan]Prompt[/bold cyan]")
        
        if user_input.lower() in ['exit', 'quit']:
            console.print("[bold red]Shutting down Neural Governor Interface...[/bold red]")
            break
            
        sys_info = get_sys_info()
        console.clear()
        
        with Live(generate_layout("Brain is processing custom command...", sys_info), refresh_per_second=4, screen=True) as live:
            time.sleep(0.5)
            initial_output = run_brain(user_input)
            live.update(generate_layout(initial_output, sys_info))

if __name__ == "__main__":
    main()
