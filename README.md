# NeuralGovernor

AI-driven, swarm-aware resource orchestrator for Android (Termux/Root).

## Overview
NeuralGovernor is a high-performance, compiled Rust binary that provides autonomous, intelligent management of CPU, Memory, and Battery health for your device.

## Features
- **Hardware-Awareness**: Dynamically identifies device SoC to apply safe, device-specific configurations.
- **Autonomous Safety**: Mandatory **Pre-flight Verification Loop** where the Brain analyzes every command for safety *before* execution.
- **Token-Efficient**: Uses lightweight, one-shot management scripts rather than heavy, continuous API streams.
- **Instant Notifications**: Utilizes system-level notifications for transparent, real-time action auditing.
- **Zero-HITL**: Fully autonomous management cycle with safety-first rejection logic.

## Use-Cases
- **Battery Optimization**: Proactively lowers CPU frequency during low-battery states.
- **Performance Management**: Automatically clears caches and optimizes scheduling during high-load scenarios.
- **Automated Safety**: Protects the device by rejecting Brain-recommended commands that fail safety analysis for your specific hardware.

## Installation
1. **Flashable Zip**: Flash the generated `resource-orchestrator.zip` via Magisk.
2. **API Configuration**: During installation, the script will prompt for your **Gemini API Key**.
3. **Boot**: Upon boot, `NeuralGovernor` will start automatically as a background daemon, managing your device resources.

## Development
- **Workflow**: Automated build workflow via GitHub Actions creates a flashable zip on every commit.
- **Security**: Hardened via Rust memory safety and explicit pre-flight command validation.
EOF
