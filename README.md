# Neural-Governor V3 🧠⚡

**Neural-Governor** is an autonomous, root-level AI system orchestrator for Android (via Magisk). It operates deep inside your device's kernel, leveraging advanced AI (Gemini Flash) to dynamically optimize performance, battery life, and thermals in real-time. 

Instead of relying on static scripts, Neural-Governor actually *thinks* about your device's current state and writes custom mitigation commands on the fly.

---

## 🏗️ How It Works (The Swarm Architecture)

Neural-Governor is powered by a decoupled, highly efficient dual-agent architecture:

### 1. The Watcher (Rust Daemon)
A native `aarch64` Rust binary running in the background 24/7. It has virtually 0% CPU footprint and checks your system telemetry (Thermals, CPU usage, Battery) every 15 seconds. 
* **Reactive Mitigation:** If your phone spikes above 45°C or battery drops critically, it instantly wakes the AI.
* **Proactive Tuning:** If the device is healthy, it wakes the AI every 15 minutes to apply background performance/battery optimizations.

### 2. The Brain (Python + AI)
The AI engine only wakes up when triggered. It receives the system telemetry snapshot, reasons about the issue, and executes a custom root shell command (e.g., tweaking ZRAM, altering CPU governors, renicing heavy tasks). If a command fails, it automatically falls back and tries a safer alternative.

---

## 🚀 Installation Guide

### Prerequisites & Dependencies
To run Neural-Governor, you need a rooted Android device with **Magisk** and **Termux** installed.

1. **Install Termux Dependencies:**
   Open Termux and install Python and the required UI library:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python -y
   pip install rich
   ```

2. **Download & Flash the Module:**
   - Go to the [Releases](https://github.com/polymath-void/Neural-Governor/releases) page.
   - Download the latest `Neural-Governor-v3.x.zip`.
   - Open Magisk Manager -> **Modules** -> **Install from storage**.
   - Select the ZIP file and flash it.
   - **Reboot your device.**

### First-Time Setup
After rebooting, the Rust Watcher is already running silently in the background! 
To set up your AI and view the dashboard:

1. Open Termux.
2. Run the dashboard using root privileges:
   ```bash
   su -c neural-dashboard
   ```
3. *Note: If this is your first time, the dashboard will prompt you to paste your free Google AI Studio (Gemini) API Key.*

---

## 💻 Using the Dashboard

The Dashboard is a pure UI that reads the AI's background execution logs so you can see exactly what the Brain is doing.

* **View Logs:** Type `/logs` in the dashboard to read a complete history of anomalies detected, the AI's reasoning, and the exact bash commands it executed.
* **Change Modes:** Type `/mode` to switch the Watcher's tuning strategy between: `Auto Pilot`, `Performance`, `Battery Saver`, or `Balanced`.
* **Manual Injection:** Type any normal prompt (e.g., *"My game is lagging, fix it"*) to manually wake the Brain and have it optimize your device on the spot.
