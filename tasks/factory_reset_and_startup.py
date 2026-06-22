"""
Factory Reset + Startup — full pipeline from wipe to Clone Phone QR screen.

Workflow:
  1. Factory reset the device via Settings → Erase all data (device reboots)
  2. Auto-detect current setup wizard screen and skip through to home
  3. Set date to random 2020–2021 epoch
  4. Delete all user files on /sdcard except Android/
  5. Open Clone Phone → Receive data → Allow permissions → QR screen

Usage:
  cd C:\Users\sarth\OneDrive\Desktop\android_automation_v.1.0.0
  python main.py factory-reset-and-startup

Options:
  --serial SERIAL    Device serial (auto-detects if omitted)
  --log-dir DIR      Directory for log files (default: current dir)

Requirements:
  - ADB + uiautomator2
  - Device with USB Debugging enabled
  - OnePlus/ColorOS device (selectors specific to OnePlus 9R)
"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.device import Device
from lib.logger import Logger
from tasks.factory_reset import FactoryResetTask
from tasks.startup import StartupTask


class FullSetupTask:
    name = "factory-reset-and-startup"
    description = "Factory reset device, skip setup wizard, clear storage, open Clone Phone"

    def run(self, device=None, logger=None):
        if logger is None:
            logger = Logger(name="full-setup", log_dir=".")
        if device is None:
            device = Device(log_dir=".")

        self.log = logger
        log = logger

        log.info("=== Full Setup: Factory Reset + Startup ===")
        steps = 2

        # --- Step 1: Factory Reset ---
        log.step(1, steps, "Factory resetting device...")
        reset = FactoryResetTask()
        if not reset.run(device=device, logger=logger):
            log.error("Factory reset failed. Aborting.")
            return False

        log.info("Factory reset complete. Device on home screen.")

        # --- Step 2: Startup (setup skip + date + clear + Clone Phone) ---
        log.step(2, steps, "Running startup automation...")
        startup = StartupTask()
        if not startup.run(device=device, logger=logger):
            log.error("Startup automation failed.")
            return False

        log.done("Full setup complete! Clone Phone ready on QR screen.")
        return True
