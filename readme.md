# Daemon Watch (DW)

Daemon Watch is a lightweight, macOS-native menu bar application built with Python. It provides a real-time, consolidated view and control interface for your background processes, specifically focusing on **Cron jobs** and **Node.js (PM2)** applications.

Designed for developers and power users, Daemon Watch eliminates the need to constantly switch to the terminal to check the status of your scheduled tasks or background services.

---

## 🚀 Key Features

### 🕒 Advanced Cron Management
Daemon Watch transforms the static `crontab` into an interactive management tool:
- **Visual Status**: Instantly see which jobs are active (🟢) or commented out/disabled (⚪️).
- **Human-Readable Schedules**: Automatically converts complex cron expressions (e.g., `*/15 * * * *`) into friendly text (e.g., "At every 15 minutes") using `cron-descriptor`.
- **On-the-Fly Editing**:
    - **Toggle**: Enable or disable jobs with a single click (automatically handles commenting in `crontab`).
    - **Custom Labels**: Assign meaningful names to your jobs. These are persisted directly in your `crontab` using `# NAME:` comments.
    - **Quick Rescheduling**: Preset options to change job frequency (Every N minutes, Daily at N, etc.) without manually editing the crontab file.
- **Immediate Execution**: Use the "Run Now" feature to trigger any cron job manually for testing or ad-hoc runs.

### 🟢 Real-time PM2 Monitoring
Stay on top of your Node.js services with integrated PM2 support:
- **Process Overview**: List all PM2-managed processes with their current status (Online 🟢 vs. Stopped/Errored 🔴).
- **Live Resource Usage**: View real-time CPU and Memory consumption for every process directly in the menu.
- **Service Control**: Quickly **Start**, **Stop**, or **Restart** services with a single click.
- **Log Access**: Open a new macOS Terminal window focused on the last 10 lines of logs for a specific process via `pm2 logs`.

### ⚙️ Intelligent Environment Integration
- **Robust Path Discovery**: Automatically detects your shell's `PATH` (zsh/bash) and common locations for `pm2`, including NVM (Node Version Manager) installations, ensuring commands work out-of-the-box.
- **Native macOS Experience**: Built on the `rumps` framework, providing a clean, non-intrusive menu bar interface that follows macOS design patterns.

---

## 🛠 Installation & Build

### 1. Prerequisites
- **macOS**: Required for the native menu bar and AppleScript integration.
- **Python 3.10+**: The core application logic.
- **PM2** (Optional): Required for process monitoring features.

### 2. Setup Environment
```bash
# Clone the repository
git clone https://github.com/roy8in/daemon-watch.git
cd daemon-watch

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Build the Application (.app)
We use `py2app` to bundle the Python script into a standalone macOS application.
```bash
# Build the standalone app
python setup.py py2app
```
The resulting application will be located in `dist/DaemonWatch.app`. You can drag this to your `/Applications` folder.

---

## 📝 Configuration & Storage
- **Cron Labels**: Labels are stored as comments directly in your crontab (e.g., `# NAME: My Backup Job`).
- **Logs**: Application logs for troubleshooting are kept at `/tmp/daemon_watch.log`.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
