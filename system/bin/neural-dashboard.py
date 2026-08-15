#!/usr/bin/env python3
import json
import time
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
LOG_FILE = "/data/local/tmp/neural_execution_history.jsonl"
BRAIN_SCRIPT = "/data/adb/modules/resource-orchestrator/system/bin/brain_wake.py"
MODE_FILE = "/data/local/tmp/neural_mode.txt"

def check_api_key():
    import os
    if not os.path.exists(CONFIG_FILE):
        return
    with open(CONFIG_FILE, "r") as f:
        for line in f:
            if line.startswith("export GEMINI_API_KEY=") and "YOUR_KEY_HERE" in line:
                console.clear()
                console.print(Panel(Align.center(Text("API Key Configuration Required", style="bold yellow"))))
                api_key = Prompt.ask("\n[bold cyan]Please paste your Google AI Studio Gemini API Key[/bold cyan]")
                if api_key:
                    new_content = f'export GEMINI_API_KEY="{api_key}"\n'
                    subprocess.run(["su", "-c", f"echo '{new_content}' > {CONFIG_FILE}"])
                    console.print("\n[bold green]API Key saved successfully![/bold green]")
                    time.sleep(1)

def read_last_logs(n=3):
    logs = []
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            for line in lines[-n:]:
                try:
                    entry = json.loads(line)
                    trigger = entry.get("user_prompt", "Autonomous Check")
                    command = entry.get("executed_command", "None")
                    resp = entry.get("brain_response", "")
                    logs.append(f"[cyan]Trigger:[/cyan] {trigger}\n[yellow]Brain:[/yellow] {resp}\n[green]Cmd:[/green] {command}")
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return logs

def view_full_logs():
    console.clear()
    console.print(Panel("[bold cyan]Last 50 Execution Logs[/bold cyan]"))
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()[-50:]
            for line in lines:
                entry = json.loads(line)
                console.print(f"[dim]{entry.get('timestamp')}[/dim] - [cyan]{entry.get('user_prompt')}[/cyan]")
                console.print(f"  [yellow]Reasoning:[/yellow] {entry.get('brain_response')}")
                console.print(f"  [green]Cmd:[/green] {entry.get('executed_command')}")
                exec_log = entry.get('execution_log', '')
                if exec_log:
                    console.print(f"  [magenta]Output:[/magenta] {exec_log.strip()}")
                console.print("-" * 40)
    except Exception as e:
        console.print(f"Could not read logs: {e}")
    Prompt.ask("\n[bold white]Press Enter to return[/bold white]")

def generate_layout(manual_output):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    header = Panel(Align.center(Text("🧠 NEURAL GOVERNOR AI STUDIO (V3) 🧠", style="bold cyan")), style="cyan")
    layout["header"].update(header)
    
    layout["main"].split_row(
        Layout(name="left_panel", ratio=1),
        Layout(name="manual_output", ratio=2)
    )
    
    # Read last 3 logs for the left panel
    last_logs = read_last_logs(3)
    log_text = "\n\n".join(last_logs) if last_logs else "No autonomous logs found."
    log_panel = Panel(Text.from_markup(log_text), title="[ Recent Watcher Autonomous Actions ]", border_style="magenta")
    layout["left_panel"].update(log_panel)
    
    manual_panel = Panel(Text.from_markup(manual_output), title="[ Manual Brain Interaction ]", border_style="yellow")
    layout["main"]["manual_output"].update(manual_panel)
    
    footer = Panel(Text("Type '/logs' to view full JSONL. Type a prompt to manually optimize. (Type 'exit' to stop)", style="dim white"), border_style="blue")
    layout["footer"].update(footer)
    
    return layout

def main():
    check_api_key()
    console.clear()
    
    manual_output = "Dashboard is active. Core daemon is running autonomously in the background.\nType a request to manually invoke the AI."
    
    while True:
        console.clear()
        console.print(generate_layout(manual_output))
        user_input = Prompt.ask("\n[bold cyan]Command/Prompt[/bold cyan]")
        
        if user_input.lower() in ['exit', 'quit']:
            console.clear()
            console.print("[bold green]Exiting Neural Governor Dashboard...[/bold green]")
            import os
            os.system('stty sane')
            break
            
        if user_input.lower().startswith("/logs"):
            view_full_logs()
            continue
            
        if user_input.lower().startswith("/mode"):
            try:
                print("Modes: 1. Auto Pilot 2. Performance 3. Battery Saver 4. Balanced")
                m = Prompt.ask("Select mode (1-4)")
                modes = ["Auto Pilot", "Performance", "Battery Saver", "Balanced"]
                idx = int(m) - 1
                if 0 <= idx < len(modes):
                    current_mode = modes[idx]
                    subprocess.run(["su", "-c", f"echo '{current_mode}' > {MODE_FILE}"])
                    subprocess.run(["su", "-c", f"chmod 666 {MODE_FILE}"])
                    manual_output = f"[bold green]Watcher Mode switched to: {current_mode}[/bold green]"
                else:
                    manual_output = "[bold red]Invalid mode selected.[/bold red]"
            except ValueError:
                manual_output = "[bold red]Invalid input.[/bold red]"
            continue
            
        if user_input.strip():
            console.clear()
            console.print(generate_layout("Contacting AI Brain for manual task... Please wait."))
            try:
                # We call the standalone brain_wake script directly for manual tasks
                # Make sure to run it as root so it has permissions
                safe_prompt = user_input.replace("'", "")
                cmd = f"su -c \"/data/data/com.termux/files/usr/bin/python3 {BRAIN_SCRIPT} 'MANUAL: {safe_prompt}'\""
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                manual_output = f"[bold]Manual Request:[/bold] {user_input}\n\n"
                
                if proc.stdout:
                    # Colorize Output
                    out_text = proc.stdout
                    out_text = out_text.replace("EXPLANATION:", "[bold yellow]EXPLANATION:[/bold yellow]")
                    out_text = out_text.replace("COMMAND:", "[bold green]COMMAND:[/bold green]")
                    out_text = out_text.replace("OUTPUT:", "[bold magenta]OUTPUT:[/bold magenta]")
                    manual_output += out_text
                if proc.stderr:
                    manual_output += f"\n[red]Error:[/red] {proc.stderr}"
            except Exception as e:
                manual_output = f"Failed to execute manual request: {e}"

if __name__ == "__main__":
    main()
