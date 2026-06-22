# Android Task Automator

> Extensible automation framework for Android devices. CLI-based, no coordinate guessing -- tasks find UI elements by **text** and **resource ID**. Add new tasks by dropping a single `.py` file.

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Win%20%7C%20Mac%20%7C%20Linux-0078D6?style=flat)]()
[![License](https://img.shields.io/badge/License-MIT-4CAF50?style=flat)](LICENSE)
[![uiautomator2](https://img.shields.io/badge/powered%20by-uiautomator2-FF6D00?style=flat)](https://github.com/openatx/uiautomator2)

---

## Why This Exists

Most Android automation scripts use **hardcoded coordinates** (`input tap 540 1900`). They break the moment you change devices, resolution, or ROM version.

This framework uses [`uiautomator2`](https://github.com/openatx/uiautomator2) -- the same engine behind Appium -- which finds UI elements by **what they say** or **their resource ID**, not where they sit on screen.

```python
# Instead of this (fragile):
adb shell input tap 540 1900

# You write this (reliable):
d(text="Erase all data").click()
```

Works on any device, any resolution, every time.

---

## Architecture

```
                        YOUR PC
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │   python main.py <task>                                 │
  │       │                                                  │
  │       ▼                                                  │
  │   main.py ──discover_tasks()──> tasks/factory_reset.py  │
  │       │                                                  │
  │       ├── lib/device.py  (connect, find, tap, swipe)     │
  │       └── lib/logger.py  (console + file + Discord)      │
  │                              │                            │
  │                              ▼ USB/WiFi                  │
  │                         ADB ────────> Android Device     │
  └──────────────────────────────────────────────────────────┘
```

The framework pushes a small agent (`atx-agent`) to the Android device once on first run.
After that, all UI queries are direct -- no XML dumps, no screen scraping.

---

## Quick Start

### 1. Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Python 3.8+** | Download from [python.org](https://python.org) |
| **ADB** (Android Debug Bridge) | [Platform Tools](https://developer.android.com/studio/releases/platform-tools) |
| **USB Debugging** | Enable on your Android device in Developer Options |
| **One USB cable** | Connect device to PC |

Verify ADB works:
```bash
adb devices
# Should show: XYZ12345  device
```

### 2. Install

```bash
# Clone
git clone https://github.com/sarthhkkk/android-task-automator.git
cd android-task-automator

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Run

```bash
# List available tasks
python main.py --list

# Run factory reset
python main.py factory-reset
```

**What happens on first run:**
1. The script connects to your device via ADB
2. It pushes `atx-agent` to the device automatically
3. It runs the task -- navigating Settings, triggering reset, skipping setup
4. Logs are written to `factory-reset.log`

---

## Usage

### CLI Reference

```bash
python main.py <task> [options]
```

| Argument | Description |
|----------|-------------|
| `<task>` | Task name (e.g., `factory-reset`) |
| `--list` | List all available tasks |
| `--serial SERIAL` | Device serial for USB (`XYZ12345`) or WiFi (`192.168.1.5:5555`) |
| `--log-dir DIR` | Directory for logs and screenshots (default: current directory) |

### Examples

```bash
# Run on first USB device
python main.py factory-reset

# Run on specific device
python main.py factory-reset --serial 192.168.1.5:5555

# Save logs elsewhere
python main.py factory-reset --log-dir ./logs
```

---

## Available Tasks

### `factory-reset`

Factory reset an Android device (OnePlus/ColorOS) and automatically skip the setup wizard.

**Flow:**
1. Connect to device
2. Open Settings and navigate to Factory Reset
3. Confirm and trigger the reset
4. Wait for device to wipe and reboot (up to 5 minutes)
5. Skip through the entire setup wizard:
   - Language / Region / Agreements
   - Wi-Fi skip
   - Google sign-in skip
   - Fingerprint skip
   - Gesture navigation
   - Complete / Get started
6. Land on home screen

**Time estimate:** 6-12 minutes total

---

## Adding New Tasks

This is the core feature. Each task is a standalone `.py` file in the `tasks/` folder. It's auto-discovered by `main.py`.

### Minimal Task

```python
# tasks/hello.py
class HelloTask:
    name = "hello"
    description = "Demonstrates how to write a task"

    def run(self, device, logger):
        logger.info("Hello from the automator!")
        device.wake()
        device.find_and_click(text="Accept")
        logger.info("Done!")
        return True
```

Save it, run it:
```bash
python main.py hello
```

No registration, no boilerplate, no changes to `main.py`.

### Task API

Every task receives two objects:

**`device`** (from `lib/device.py`):

| Method | What it does |
|--------|-------------|
| `connect()` | Connect to device via ADB |
| `reconnect(timeout)` | Wait for device to come back after reboot |
| `wake()` | Turn screen on + swipe to unlock |
| `find_and_click(text=..., resource_id=..., cls=..., timeout=...)` | Find UI element by text/ID/class and tap it |
| `find_and_click_all([texts...], timeout=...)` | Try multiple text matches, click first found |
| `swipe_down()` / `swipe_up()` | Scroll down/up |
| `screenshot(name)` | Take screenshot (saved to `screenshots/`) |
| `current_focus()` | Get current focused activity/screen name |
| `go_home()` | Press Home button |
| `back()` | Press Back button |

**`logger`** (from `lib/logger.py`):

| Method | What it does |
|--------|-------------|
| `info(msg)` | Log info to console + file |
| `warn(msg)` | Log warning |
| `error(msg)` | Log error |
| `step(num, total, msg)` | Log a progress step |
| `done(msg)` | Log completion |
| `discord(title, description, color)` | Send to Discord webhook (if configured) |

---

## Discord Notifications

Set the environment variable and the logger will send task updates to your Discord channel:

```bash
set AUTOMATOR_DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
python main.py factory-reset
```

Each task sends:
- Start notification (when task begins)
- Done/failure notification (when task ends)

---

## Device Connection

### USB

Connect via USB cable. The script auto-detects the first available device:

```bash
python main.py factory-reset
```

### WiFi (no cable)

```bash
# First, connect via USB and set up TCP/IP
adb tcpip 5555
# Disconnect USB, then:
adb connect 192.168.1.5:5555

# Now run:
python main.py factory-reset --serial 192.168.1.5:5555
```

### Multiple Devices

List connected devices:
```bash
adb devices
#   emulator-5554  device
#   XYZ12345       device
```

Target a specific one:
```bash
python main.py factory-reset --serial XYZ12345
```

---

## Troubleshooting

### `uiautomator2` connection fails
First run takes 10-15 seconds as it pushes `atx-agent` to the device. Ensure USB debugging is **enabled** and the device screen is **unlocked** when the script starts.

### `adb: device unauthorized`
Accept the RSA fingerprint prompt on the device screen.

### Script stuck during setup wizard
The 10-minute timeout will fire and the script will exit. Take a screenshot first:
```python
# Add to your task:
device.screenshot("stuck_screen")
```
Then check `screenshots/stuck_screen.png`.

### Device doesn't reconnect after reset
Factory reset takes 5-10 minutes on most devices. The script waits up to 5 minutes. If it times out, the device might still be wiping -- wait and check `adb devices`.

### `pip install` fails on Windows
If you get a build error for `cryptography`, install Microsoft C++ Build Tools from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

---

## Project Structure

```
android-task-automator/
│
├── main.py                  # CLI entry point -- python main.py <task>
│
├── lib/
│   ├── __init__.py
│   ├── device.py            # Device connection, UI interaction
│   └── logger.py            # Console + file + Discord logging
│
├── tasks/
│   ├── __init__.py
│   └── factory_reset.py     # Factory reset + setup wizard skip
│
├── requirements.txt         # uiautomator2, Pillow
├── .gitignore
└── README.md                # This file
```

---

## Roadmap

- [x] Factory reset + setup skip
- [x] Modular task system (drop-in `.py` files)
- [x] WiFi device support
- [x] Discord notifications
- [x] Screenshot on failure
- [ ] Install APK batch task
- [ ] Configure Wi-Fi task
- [ ] Bulk device operations
- [ ] PyInstaller single .exe build

---

## License

MIT -- see [LICENSE](LICENSE).

Built on [`uiautomator2`](https://github.com/openatx/uiautomator2).
