import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.device import Device
from lib.logger import Logger


class FactoryResetTask:
    name = "factory-reset"
    description = "Factory reset an Android device and skip the setup wizard"

    def run(self, device=None, logger=None):
        if logger is None:
            logger = Logger(name="factory-reset", log_dir=".")
        if device is None:
            device = Device(log_dir=".")

        logger.info("=== Factory Reset Task ===")
        steps = 5

        # Step 1: Connect
        logger.step(1, steps, "Connecting to device...")
        try:
            device.connect()
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
        logger.info(f"Device: {device.width}x{device.height}")

        # Step 2: Navigate to Factory Reset
        logger.step(2, steps, "Navigating to factory reset...")
        self._navigate_to_reset(device, logger)

        # Step 3: Confirm and trigger reset
        logger.step(3, steps, "Triggering factory reset...")
        self._trigger_reset(device, logger)

        # Step 4: Wait for reboot
        logger.step(4, steps, "Waiting for device to reboot...")
        logger.info("Device should disconnect now. Waiting for wipe + reboot...")
        try:
            device.reconnect(timeout=300)
            logger.info("Device reconnected after reset")
        except TimeoutError:
            logger.error("Device did not reconnect within 5 minutes")
            return False

        # Step 5: Skip setup wizard
        logger.step(5, steps, "Skipping setup wizard...")
        self._skip_setup(device, logger)

        device.go_home()
        logger.done("Factory reset completed. Device is on home screen.")
        return True

    def _navigate_to_reset(self, d, log):
        log.info("Waking device...")
        d.wake()
        time.sleep(2)

        log.info("Opening Settings...")
        d.d.app_start("com.android.settings")
        time.sleep(3)

        log.info("Searching for reset options...")
        found = d.find_and_click_all([
            "Back up & reset",
            "Backup & reset",
            "Reset options",
            "Reset phone",
            "Factory reset",
            "Erase all data",
            "System",
            "Additional settings",
            "Additional Settings",
        ], timeout=5)

        if not found:
            log.info("Scrolling down to find reset options...")
            for _ in range(5):
                d.swipe_down()
                time.sleep(1)
                if d.find_and_click_all([
                    "Back up & reset",
                    "Reset options",
                    "Factory reset",
                    "Erase all data",
                ], timeout=2):
                    break

        time.sleep(2)
        d.find_and_click_all([
            "Back up & reset",
            "Reset options",
            "Factory reset",
            "Erase all data (factory reset)",
            "Erase all data",
            "Reset phone",
        ], timeout=5)

    def _trigger_reset(self, d, log):
        confirm_texts = [
            "Erase all data",
            "Erase everything",
            "Reset phone",
            "Reset",
            "Confirm",
            "Delete all",
            "Clear all",
        ]
        found = d.find_and_click_all(confirm_texts, timeout=5)
        if not found:
            log.info("Trying bottom-center tap as fallback...")
            d.d.click(d.width // 2, int(d.height * 0.85))
            time.sleep(2)
            d.d.click(d.width // 2, int(d.height * 0.84))

        time.sleep(3)
        log.info("Factory reset command sent. Device should reboot.")

    def _skip_setup(self, d, log):
        log.info("Waiting for setup wizard...")
        time.sleep(5)

        log.info("Trying fast path (direct flags)...")
        d.d.shell(["settings", "put", "global", "device_provisioned", "1"])
        d.d.shell(["settings", "put", "secure", "user_setup_complete", "1"])
        d.d.shell(["settings", "put", "global", "setup_wizard_has_run", "1"])
        time.sleep(2)

        if self._is_home(d):
            log.info("Fast path worked! Already on home screen.")
            return

        log.info("Walking through setup wizard screens...")
        deadline = time.time() + 600
        step = 1
        setup_actions = [
            ("Start", d.find_and_click, ["Start"]),
            ("Continue", d.find_and_click, ["Continue"]),
            ("Skip", d.find_and_click, ["Skip"]),
            ("Not now", d.find_and_click, ["Not now"]),
            ("Accept", d.find_and_click, ["Accept"]),
            ("Agree", d.find_and_click, ["Agree"]),
            ("Next", d.find_and_click, ["Next"]),
            ("Done", d.find_and_click, ["Done"]),
            ("Get started", d.find_and_click, ["Get started"]),
            ("Set up later", d.find_and_click, ["Set up later"]),
            ("Remind me later", d.find_and_click, ["Remind me later"]),
            ("Skip anyway", d.find_and_click, ["Skip anyway"]),
        ]

        while time.time() < deadline:
            focus = d.current_focus().lower()
            if self._is_home(d):
                log.info("Home screen detected. Setup complete!")
                return

            acted = False
            for label, action, args in setup_actions:
                if action(*args, timeout=1):
                    log.step(step, 99, f"Tapped '{label}'")
                    step += 1
                    acted = True
                    time.sleep(2)
                    break

            if not acted:
                log.info(f"Unknown screen, waiting... ({focus[:60]})")
                time.sleep(5)
                step += 1

            if step > 120:
                log.error("Too many attempts. Giving up.")
                d.screenshot("setup_timeout")
                break

        log.info("Setup wizard navigation finished.")

    def _is_home(self, d):
        focus = d.current_focus().lower()
        return any(x in focus for x in ["launcher", "home", "desktop"])
