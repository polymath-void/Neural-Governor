# Neural-Governor V3

**Neural-Governor** is an autonomous, root-level AI system orchestrator for Android (via Magisk). It monitors device telemetry at the kernel level and leverages advanced AI (Gemini Flash APIs) to dynamically optimize performance, battery life, and thermals in real-time.

## Architecture

Neural-Governor V3 introduces a decoupled "Watcher-Brain" architecture:

1. **The Rust Watcher (`resource-orchestrator`)**
   - Runs 24/7 as a lightweight Magisk daemon.
   - Constantly gathers telemetry (Thermals, CPU spikes, Battery level).
   - **Reactive Mode**: Instantly detects anomalies (e.g., Thermals > 45°C) and wakes the Brain for emergency mitigation.
   - **Proactive Mode (Auto-Pilot)**: Wakes the Brain every 15 minutes to proactively tune the system based on the user's selected mode (Performance, Battery Saver, etc.).

2. **The Python Brain (`brain_wake.py`)**
   - A standalone execution engine that wakes up only when triggered.
   - Queries `gemini-3.1-flash-lite` (or fallback) with the system anomaly and context.
   - Safely executes bash commands as root to optimize the system (ZRAM tuning, renicing, CPU governor tweaks).
   - Logs everything into a `jsonl` file for offline model training and transparency.
   - Sleeps immediately after execution to conserve 100% of background CPU.

3. **The Interactive Dashboard (`neural-dashboard.py`)**
   - A pure, Termux-based UI (using `rich`) that reads the `jsonl` log files.
   - Displays real-time hardware status and a rolling log of recent AI autonomous actions.
   - Allows users to change modes via `/mode` (Auto Pilot, Performance, Battery Saver, Balanced).
   - Allows manual prompt injection for custom AI commands.

## Installation
1. Flash the `Neural-Governor.zip` module in Magisk.
2. Reboot the device.
3. Open Termux and run `neural-dashboard`.
4. (First run only) Paste your Google AI Studio API Key.

## Logs & Transparency
All background autonomous actions are logged in `JSON Lines` format to `/data/local/tmp/neural_execution_history.jsonl`.
Use `/logs` inside the dashboard to view them in a human-readable format.
