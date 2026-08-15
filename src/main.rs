use anyhow::{anyhow, Result};
use std::process::Command;
use std::fs;
use std::path::Path;
use serde::{Deserialize, Serialize};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH, Duration};

#[derive(Debug, Serialize)]
struct SystemSnapshot {
    cpu_stat: String,
    mem_info: String,
    battery: String,
    thermal: String,
    soc_info: String,
    active_tasks: String,
}

fn collect_snapshot() -> Result<SystemSnapshot> {
    let cpu_stat = fs::read_to_string("/proc/stat").unwrap_or_default().lines().next().unwrap_or("").to_string();
    let mem_info = fs::read_to_string("/proc/meminfo").unwrap_or_default().lines().take(3).collect::<Vec<_>>().join(" | ");
    let battery = fs::read_to_string("/sys/class/power_supply/battery/capacity").unwrap_or_else(|_| "100".to_string()).trim().to_string();
    
    // Attempt thermal
    let thermal = fs::read_to_string("/sys/class/thermal/thermal_zone0/temp").unwrap_or_else(|_| "0".to_string()).trim().to_string();
    
    let soc_info = fs::read_to_string("/proc/cpuinfo").unwrap_or_default().lines().find(|l| l.contains("Hardware")).unwrap_or("Unknown").to_string();
    
    // Grab top tasks (very basic)
    let active_tasks = match Command::new("top").args(["-n", "1", "-m", "5"]).output() {
        Ok(output) => String::from_utf8_lossy(&output.stdout).lines().take(6).collect::<Vec<_>>().join("\n"),
        Err(_) => "Unknown".to_string()
    };

    Ok(SystemSnapshot { cpu_stat, mem_info, battery, thermal, soc_info, active_tasks })
}

// Write the snapshot to a known shared location for the brain
fn write_snapshot_for_brain(snapshot: &SystemSnapshot) -> Result<()> {
    let json = serde_json::to_string(snapshot)?;
    fs::write("/data/local/tmp/neural_snapshot.json", &json)?;
    let _ = Command::new("chmod").args(["666", "/data/local/tmp/neural_snapshot.json"]).status();
    Ok(())
}

fn check_path_writable(path: &str) -> bool {
    let p = Path::new(path);
    p.exists() && fs::OpenOptions::new().write(true).open(p).is_ok()
}

fn execute_action(action: &str) -> Result<String> {
    // If it's a file write, check if possible, fallback if not
    if action.contains(">") {
        let parts: Vec<&str> = action.split('>').collect();
        if parts.len() == 2 {
            let file_path = parts[1].trim();
            if !check_path_writable(file_path) {
                // Fallback action, kernel path locked
                let fallback = format!("log -t NeuralGovernor 'Locked path: {} - falling back to renice'", file_path);
                Command::new("su").args(["-c", &fallback]).output()?;
                return Err(anyhow!("Kernel path locked: {}", file_path));
            }
        }
    }

    let output = Command::new("su").args(["-c", action]).output()?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(anyhow!("Execution failed: {}", String::from_utf8_lossy(&output.stderr)))
    }
}

fn analyze_snapshot(snap: &SystemSnapshot) -> Option<String> {
    if let Ok(temp) = snap.thermal.parse::<i32>() {
        if temp > 45000 {
            return Some(format!("High thermal anomaly detected: {} millidegrees.", temp));
        }
    }
    if let Ok(bat) = snap.battery.parse::<i32>() {
        if bat <= 25 {
            return Some(format!("Battery critical anomaly: {}%. Apply extreme power saving.", bat));
        }
    }
    
    // Very basic CPU spike detection from active tasks string (heuristic)
    if snap.active_tasks.contains(" 9") && snap.active_tasks.contains(".") || snap.active_tasks.contains("100.") {
        return Some("High CPU usage spike detected in top tasks.".to_string());
    }
    
    None
}

fn daemon_loop() {
    println!("Starting Neural-Governor Sub-Booster Daemon...");
    let mut last_trigger_time = 0;
    let mut last_periodic_time = 0;
    loop {
        if let Ok(snapshot) = collect_snapshot() {
            let _ = write_snapshot_for_brain(&snapshot);
            
            // Analyze and potentially wake the brain for emergencies
            if let Some(anomaly) = analyze_snapshot(&snapshot) {
                let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
                // Cooldown: only trigger at most once every 5 minutes (300 seconds)
                if now - last_trigger_time > 300 {
                    let safe_anomaly = anomaly.replace("'", "");
                    let cmd = format!("python3 /data/adb/modules/resource-orchestrator/system/bin/brain_wake.py '{}'", safe_anomaly);
                    let _ = Command::new("su").args(["-c", &cmd]).status();
                    last_trigger_time = now;
                    last_periodic_time = now; // reset periodic timer
                }
            } else {
                // No emergency anomaly. Execute proactive Auto Pilot / Mode optimization check every 15 minutes.
                let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
                if now - last_periodic_time > 900 {
                    let current_mode = fs::read_to_string("/data/local/tmp/neural_mode.txt").unwrap_or_else(|_| "Auto Pilot".to_string());
                    let proactive_prompt = format!("PROACTIVE TUNING: System is stable. Current Mode is {}. Apply safe governor, paging, and kernel tweaks to optimize for this mode without causing instability.", current_mode.trim());
                    let cmd = format!("python3 /data/adb/modules/resource-orchestrator/system/bin/brain_wake.py '{}'", proactive_prompt);
                    let _ = Command::new("su").args(["-c", &cmd]).status();
                    last_periodic_time = now;
                    last_trigger_time = now;
                }
            }
            
            // Process any manual actions queued by the dashboard
            if let Ok(action) = fs::read_to_string("/data/local/tmp/neural_action.txt") {
                if !action.trim().is_empty() {
                    let _ = execute_action(action.trim());
                    let _ = fs::write("/data/local/tmp/neural_action.txt", "");
                    let _ = Command::new("chmod").args(["666", "/data/local/tmp/neural_action.txt"]).status();
                }
            }
        }
        // Sleep heavily to prevent battery drain
        thread::sleep(Duration::from_secs(10));
    }
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.contains(&"--daemon".to_string()) {
        daemon_loop();
    } else {
        println!("Neural-Governor 2.0 - Use --daemon for background monitoring.");
        // One shot snapshot
        let snap = collect_snapshot()?;
        let json = serde_json::to_string_pretty(&snap)?;
        println!("Current Snapshot:\n{}", json);
    }
    Ok(())
}
