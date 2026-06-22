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

        self.log = logger

        logger.info("=== New Phone Startup Automation ===")

        try:
            device.connect()
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

        self.d = device.d
        d = self.d
        log = self.log

        log.info(f"Device: {device.width}x{device.height}")

        current = self._detect_step(d)
        log.info(f"Detected at step {current}: {self._step_label(current)}")

        self._run_steps_from(d, current)

        log.done("Startup automation complete!")
        return True

    def _step_label(self, idx):
        labels = [
            "Hello swipe",
            "Language -> Next",
            "Region -> Next",
            "Legal -> Next",
            "Wi-Fi -> Skip",
            "Copy data -> Don't copy",
            "Google sign-in -> Skip x2",
            "Google services -> More x2 -> Accept",
            "Unlock method -> Skip",
            "Review apps -> OK",
            "Red Cable Club -> Skip",
            "Navigation -> Gestures -> Next",
            "Features -> Done",
            "Get started",
            "Home screen",
            "Set date",
            "Clear storage",
            "Open Clone Phone",
        ]
        return labels[idx] if idx < len(labels) else "Unknown"

    def _detect_step(self, d):
        xml = d.dump_hierarchy()

        markers = [
            "Hello",
            "Select language",
            "Select region",
            "Legal information",
        ]

        for i, marker in enumerate(markers):
            if marker in xml:
                return i

        if "Select network" in xml or "Choose a network" in xml:
            return 4

        if "Don" in xml and "copy" in xml.lower():
            return 5

        if "Sign in" in xml or "Google" in xml:
            if "More" in xml or "Accept" in xml:
                return 7
            return 6

        if "More" in xml:
            return 7

        if "unlock" in xml.lower():
            return 8

        if "OK" in xml and "additional" in xml.lower():
            return 9

        if "Red Cable Club" in xml:
            return 10

        if "Gestures" in xml:
            return 11

        if "Done" in xml:
            return 12

        if "Get started" in xml:
            return 13

        app = d.app_current()
        pkg = app.get("package", "")

        if "com.oneplus.backuprestore" in pkg:
            return 17

        if "launcher" in pkg or "home" in pkg:
            result = d.shell(["date", "+%s"])
            epoch_str = result.output.strip()
            if epoch_str.isdigit():
                epoch = int(epoch_str)
                if 1577836800 <= epoch <= 1640995199:
                    result2 = d.shell(["ls", "-A", "/sdcard/"])
                    entries = [e for e in result2.output.split() if e not in ("DCIM",)]
                    if entries == ["Android"]:
                        return 17
                    return 16
            return 14

        return 0

    def _run_steps_from(self, d, start):
        steps = [
            (lambda: d.swipe(900, 1500, 100, 1500, 0.3), "Hello screen -> swipe left"),
            (lambda: self._tap_right_button(d), "Language -> Next"),
            (lambda: self._tap_right_button(d), "Region -> Next"),
            (lambda: d(text="Next").click(), "Legal -> Next"),
            (lambda: (
                d(text="Skip").click(),
                self._wait_for_loading(d)
            ), "Wi-Fi -> Skip"),
            (lambda: (
                d(textContains="Don").click(),
                self._wait_for_loading(d, text_check="Checking info")
            ), "Copy data -> Don't copy"),
            (lambda: (
                d(text="Skip").click(), time.sleep(3),
                d(text="Skip").click(), time.sleep(3)
            ), "Google sign-in -> Skip x2"),
            (lambda: (
                d(text="More").click(), time.sleep(2),
                d(text="More").click(), time.sleep(2),
                d(text="Accept").click(), time.sleep(3)
            ), "Google services -> More x2 -> Accept"),
            (lambda: d(text="Skip").click(), "Unlock method -> Skip"),
            (lambda: (
                d(text="OK").click(),
                self._wait_for_loading(d)
            ), "Review apps -> OK"),
            (lambda: d(text="Skip").click(), "Red Cable Club -> Skip"),
            (lambda: (
                d(text="Gestures").click(), time.sleep(1),
                d(text="Next").click()
            ), "Navigation -> Gestures -> Next"),
            (lambda: d(text="Done").click(), "Features -> Done"),
            (lambda: d(text="Get started").click(), "Get started"),
        ]

        for i, (fn, label) in enumerate(steps):
            if i < start:
                self.log.info(f"Skipping (already past): {label}")
                continue
            time.sleep(2)
            self._run_step(label, fn)
            time.sleep(1)

        self.log.info("Setup wizard complete! On home screen.")

        post_steps = [
            (lambda: self._set_random_date(d), "Set date to random 2020-2021", 15),
            (lambda: self._clear_storage(d), "Clear storage (except Android/)", 16),
            (lambda: self._setup_clone_phone(d), "Open Clone Phone", 17),
        ]

        for fn, label, step_idx in post_steps:
            if step_idx < start:
                self.log.info(f"Skipping (already past): {label}")
                continue
            time.sleep(2)
            self._run_step(label, fn)
            time.sleep(1)

    def _run_step(self, label, fn, max_retries=3):
        for attempt in range(1, max_retries + 1):
            try:
                fn()
                self.log.info(f"OK: {label}")
                return True
            except Exception as e:
                self.log.error(f"FAIL (attempt {attempt}/{max_retries}): {label} — {e}")
                if attempt < max_retries:
                    self.log.warning(f"Auto-retrying: {label}")
                    time.sleep(2)
                else:
                    self.log.warning(f"Skipping after {max_retries} failures: {label}")
        return False

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
        start = 1577836800
        end = 1640995199
        epoch = random.randint(start, end)
        d.shell(["cmd", "alarm", "set-time", str(epoch)])

    def _clear_storage(self, d):
        cmd = "cd /sdcard && for f in *; do [ \"$f\" != \"Android\" ] && rm -rf \"$f\"; done"
        d.shell(["sh", "-c", cmd])
        self.log.info("Storage cleared (Android/ preserved).")

    def _setup_clone_phone(self, d):
        d.press("home")
        time.sleep(2)
        d.app_start("com.oneplus.backuprestore")
        time.sleep(5)

        d.shell(["wm", "dismiss-keyguard"])
        time.sleep(2)

        d(text="Receive data").click()
        time.sleep(3)

        for _ in range(10):
            allow = d(text="Allow")
            if allow.exists:
                allow.click()
                time.sleep(3)
            else:
                break

        time.sleep(3)

        d(text="OPPO, realme or OnePlus").click()
        time.sleep(3)

        self.log.info("Clone Phone ready on QR screen.")
