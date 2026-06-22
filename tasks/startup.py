import time
import sys
import os
import random
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.device import Device
from lib.logger import Logger


class StartupTask:
    name = "startup"
    description = "Automate new phone setup wizard for OnePlus/ColorOS"

    def run(self, device=None, logger=None):
        if logger is None:
            logger = Logger(name="startup", log_dir=".")
        if device is None:
            device = Device(log_dir=".")

        logger.info("=== New Phone Startup Automation ===")

        try:
            device.connect()
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

        d = device.d
        log = logger

        log.info(f"Device: {device.width}x{device.height}")

        # Step 1: Hello screen -> Next
        log.step(1, 99, "Hello screen -> Next")
        self._tap_next(d)
        time.sleep(3)

        # Step 2: Language selection -> Next
        log.step(2, 99, "Language -> Next")
        self._tap_right_button(d)
        time.sleep(3)

        # Step 3: Region selection -> Continue
        log.step(3, 99, "Region -> Continue")
        el = d(text="Continue")
        if el.exists:
            el.click()
            log.info("Tapped Continue")
        else:
            self._tap_right_button(d)
        time.sleep(3)

        # Step 4: Legal information -> Next
        log.step(4, 99, "Legal -> Next")
        d(text="Next").click()
        time.sleep(3)

        # Step 5: Wi-Fi -> Skip
        log.step(5, 99, "Wi-Fi -> Skip")
        d(text="Skip").click()
        self._wait_for_loading(d)

        # Step 6: Copy apps and data -> Don't copy
        log.step(6, 99, "Copy data -> Don't copy")
        d(textContains="Don").click()
        self._wait_for_loading(d, text_check="Checking info")

        # Step 7: Google sign-in -> Skip -> Skip dialog
        log.step(7, 99, "Google sign-in -> Skip")
        d(text="Skip").click()
        time.sleep(3)
        d(className="android.widget.Button", instance=1).click()
        time.sleep(3)

        # Step 8: Google services -> Accept
        log.step(8, 99, "Google services -> Accept")
        d(text="More").click()
        time.sleep(2)
        device.swipe_down()
        time.sleep(2)
        d(text="Accept").click()
        time.sleep(3)

        # Step 9: Unlock method -> Skip
        log.step(9, 99, "Unlock method -> Skip")
        d(text="Skip").click()
        time.sleep(3)

        # Step 10: Review additional apps -> OK
        log.step(10, 99, "Review apps -> OK")
        d(text="OK").click()
        self._wait_for_loading(d)

        # Step 11: Red Cable Club -> Skip
        log.step(11, 99, "Red Cable Club -> Skip")
        d(text="Skip").click()
        time.sleep(3)

        # Step 12: Navigation method -> Gestures -> Next
        log.step(12, 99, "Navigation -> Gestures")
        d(text="Gestures").click()
        time.sleep(1)
        d(text="Next").click()
        time.sleep(3)

        # Step 13: Recommended features -> Done
        log.step(13, 99, "Features -> Done")
        d(text="Done").click()
        time.sleep(3)

        # Step 14: Complete -> Get started
        log.step(14, 99, "Complete -> Get started")
        d(text="Get started").click()
        time.sleep(5)

        log.info("Setup wizard complete! On home screen.")

        # Step 15: Set date to random 2020-2021
        log.step(15, 99, "Setting date to random 2020-2021...")
        self._set_random_date(d)
        time.sleep(2)

        # Step 16: Open Clone Phone and navigate to QR screen
        log.step(16, 99, "Opening Clone Phone...")
        self._setup_clone_phone(d)

        log.done("Startup automation complete!")
        return True

    def _tap_next(self, d):
        nxt = d(description="Next")
        if nxt.exists:
            nxt.click()
            return
        nxt = d(text="Next")
        if nxt.exists:
            nxt.click()
            return
        self._tap_right_button(d)

    def _tap_right_button(self, d):
        btn = d(resourceId="com.coloros.bootreg:id/btn_bottom_control_right")
        if btn.exists:
            btn.click()

    def _wait_for_loading(self, d, text_check="Getting your phone ready", timeout=180):
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(5)
            xml = d.dump_hierarchy()
            if text_check not in xml:
                return True
        return False

    def _set_random_date(self, d):
        # Random date between 2020-01-01 and 2021-12-31
        start = 1577836800  # 2020-01-01 00:00:00 UTC
        end = 1640995199  # 2021-12-31 23:59:59 UTC
        epoch = random.randint(start, end)
        d.shell(["settings", "put", "global", "auto_time", "0"])
        time.sleep(1)
        d.shell(["cmd", "alarm", "set-time", str(epoch * 1000)])

    def _setup_clone_phone(self, d):
        d.press("home")
        time.sleep(2)
        d.app_start("com.oneplus.backuprestore")
        time.sleep(5)

        d.shell(["wm", "dismiss-keyguard"])
        time.sleep(2)

        # Tap "This is the new device" -> "Receive data"
        d(text="This is the new device").click()
        time.sleep(2)
        d(text="Receive data").click()
        time.sleep(3)

        # Allow all permissions
        for _ in range(10):
            allow = d(text="Allow")
            if allow.exists:
                allow.click()
                time.sleep(3)
            else:
                break

        time.sleep(3)

        # Select "OPPO, realme or OnePlus"
        d(text="OPPO, realme or OnePlus").click()
        time.sleep(3)

        log.info("Clone Phone ready on QR screen.")
