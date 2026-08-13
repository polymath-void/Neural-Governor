# 🧠 Neural-Governor

AI-driven, swarm-aware resource orchestrator for Android (Termux/Root/Magisk).

## Overview
Neural-Governor is a high-performance, compiled Rust binary that provides autonomous, intelligent management of CPU, Memory, and Battery health for your device. It integrates with the **Polymath-Void** architecture to inject AI logic directly into the Android system layer.

## ✨ Features
- **Hardware-Awareness**: Dynamically identifies device SoC to apply safe, device-specific configurations.
- **Autonomous Safety**: Mandatory **Pre-flight Verification Loop** where the Brain analyzes every command for safety *before* execution.
- **Interactive TUI Dashboard**: Shipped with `neural-dashboard` — a stunning Python/Rich Terminal UI that provides real-time visibility into brain processing, system metrics, and allows you to send **custom prompts** directly to the AI orchestrator.
- **Token-Efficient**: Uses lightweight, one-shot management scripts rather than heavy, continuous API streams.
- **Instant Notifications**: Utilizes system-level notifications for transparent, real-time action auditing.
- **Automated CI/CD Pipeline**: GitHub Actions automatically compile the Rust binary, build the Magisk module, bundle dependencies, and publish a flashable zip on every push.

## 🚀 Installation
1. **Download**: Grab the latest flashable `.zip` artifact from the **Releases** page.
2. **Flash via Magisk**: Install the zip through the Magisk app or a custom recovery. 
   *(Note: The flashing process will automatically install Termux dependencies like Python and Rich for the TUI).*
3. **API Configuration**: Ensure your Gemini API Key is configured. *(Check the internal script or define it via `/sdcard/gemini_api.txt` if using the Magisk App UI).*
4. **Boot**: Upon boot, `Neural-Governor` is ready to autonomously manage your device resources.

## 💻 Using the Dashboard (TUI)
Once the Magisk module is installed, you can monitor the AI's internal reasoning and take manual control from anywhere in Termux. 

Open Termux and run:
```bash
neural-dashboard
```
This will open the fully interactive Terminal UI where you can monitor the hardware context or pass custom reasoning commands straight to the brain.

## 🛠 Development & Architecture
- **Rust Engine**: Written in Rust (`src/main.rs`) and compiled via `cargo-ndk` targeting `aarch64-linux-android`.
- **Dashboard Interface**: Python `rich` wrapper (`polymath_cli.py`) stored in `system/bin/neural-dashboard`.
- **Workflow**: Automated build workflow via `.github/workflows/build.yml` creates a release zip automatically.
- **Security**: Hardened via Rust memory safety and explicit pre-flight command validation.
