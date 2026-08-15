# Neural-Governor Agent Swarm Architecture

Neural-Governor V3 operates using a localized Swarm Architecture to ensure the device remains stable and highly performant without human intervention. 

## The Watcher Agent (Rust Daemon)
**Role:** System Telemetry & Event Triggering
**Location:** `/data/adb/modules/resource-orchestrator/system/bin/resource-orchestrator`
**Behavior:**
- Runs continuously (24/7) with virtually 0% CPU footprint.
- **Reactive Analysis:** Checks `/proc/stat`, `/sys/class/thermal`, and `top` every 15 seconds.
- **Trigger Conditions:** 
  - Thermal exceeds 45°C.
  - Battery drops below 25%.
  - High CPU spike (Heuristic).
- **Proactive Auto-Pilot:** If no anomalies occur, wakes the Brain Agent every 15 minutes for baseline tuning (respecting user modes like `Performance` or `Battery Saver`).

## The Brain Agent (Python + LLM)
**Role:** Reasoning & Execution
**Location:** `/data/adb/modules/resource-orchestrator/system/bin/brain_wake.py`
**Behavior:**
- Only wakes when called by the Watcher Agent or manually by the User.
- Uses `gemini-3.1-flash-lite` (or fallback) to reason over the anomaly.
- Writes and executes root bash scripts natively to solve the issue (e.g., tweaking ZRAM, altering CPU governors, renicing processes).
- **Auto-Fallback Mechanism:** If a generated bash command fails (exit code != 0), it intercepts the `stderr` and queries the LLM again for a safer alternative command.
- **Logging Pipeline:** Safely documents the entire interaction (Context -> AI Reasoning -> Shell Command -> Output) into `/data/local/tmp/neural_execution_history.jsonl` for offline dataset generation.

## The Dashboard Agent (User Interface)
**Role:** Transparency & Manual Override
**Location:** `/data/adb/modules/resource-orchestrator/system/bin/neural-dashboard.py` (Termux Wrapper)
**Behavior:**
- Provides a clean Termux TUI separating backend autonomous logs from manual user requests.
- Reads the JSONL file to surface the latest autonomous actions to the user.
- Allows mode switching (`/mode`) which saves to `/data/local/tmp/neural_mode.txt` for the Watcher Agent to respect during its 15-minute proactive cycles.
