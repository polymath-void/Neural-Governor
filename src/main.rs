use anyhow::{anyhow, Result};
use std::process::Command;
use std::fs;
use serde::{Deserialize, Serialize};

// 1. Comprehensive Device Snapshot
#[derive(Debug, Serialize)]
struct SystemSnapshot {
    cpu_stat: String,
    mem_info: String,
    battery: String,
    thermal: String,
    soc_info: String,
}

fn collect_snapshot() -> Result<SystemSnapshot> {
    let cpu_stat = fs::read_to_string("/proc/stat")?.lines().next().unwrap_or("").to_string();
    let mem_info = fs::read_to_string("/proc/meminfo")?.lines().next().unwrap_or("").to_string();
    let battery = fs::read_to_string("/sys/class/power_supply/battery/capacity")?.trim().to_string();
    
    // Thermal: Get temp from first thermal zone
    let thermal = fs::read_to_string("/sys/class/thermal/thermal_zone0/temp").unwrap_or_else(|_| "0".to_string());
    
    // SoC Info: Comprehensive identification
    let soc_info = fs::read_to_string("/proc/cpuinfo")?.to_string();
    
    Ok(SystemSnapshot { cpu_stat, mem_info, battery, thermal, soc_info })
}

// 2. Notifications
fn notify_system(title: &str, message: &str) -> Result<()> {
    let _ = Command::new("termux-notification")
        .args(["--title", title, "--content", message])
        .status()?;
    Ok(())
}

// 3. Automated Safety Validation (Pre-flight)
fn pre_flight_verify(_snapshot: &SystemSnapshot, cmd: &str) -> Result<bool> {
    println!("Brain pre-flight analysis for command: {}", cmd);
    // Placeholder: This is where Gemini API will analyze hardware context vs command
    let is_safe = !cmd.contains("rm -rf") && !cmd.contains("/dev/block/");
    Ok(is_safe)
}

// 4. Execution Engine with Verification
fn execute_action(snapshot: &SystemSnapshot, action: &str) -> Result<String> {
    if !pre_flight_verify(snapshot, action)? {
        let _ = notify_system("Orchestrator Security", &format!("Rejected unsafe command: {}", action));
        return Err(anyhow!("Pre-flight verification failed!"));
    }

    let output = Command::new("su").args(["-c", action]).output()?;
    
    if output.status.success() {
        let res = String::from_utf8_lossy(&output.stdout).to_string();
        let _ = notify_system("Orchestrator Success", &format!("Action: {} | Result: {}", action, res));
        Ok(res)
    } else {
        let err = String::from_utf8_lossy(&output.stderr).to_string();
        let _ = notify_system("Orchestrator Error", &format!("Action: {} | Error: {}", action, err));
        Err(anyhow!("Execution failed: {}", err))
    }
}

// 5. Brain Logic (Hardware-Aware)
fn get_brain_recommendation(snapshot: &SystemSnapshot) -> String {
    println!("Brain analyzing hardware: {}", snapshot.soc_info.lines().next().unwrap_or("Unknown"));
    
    // Safety Filter: Hardcoded for demonstration.
    if snapshot.battery.parse::<i32>().unwrap_or(100) < 20 {
        "echo powersave > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor".to_string()
    } else {
        "sync; echo 3 > /proc/sys/vm/drop_caches".to_string()
    }
}

fn main() -> Result<()> {
    let snapshot = collect_snapshot()?;
    let action = get_brain_recommendation(&snapshot);
    let result = execute_action(&snapshot, &action)?;
    println!("Action result: {}", result);
    Ok(())
}
