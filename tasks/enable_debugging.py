import subprocess
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.logger import Logger


class EnableDebuggingTask:
    name = "enable-debugging"
    description = "Enable USB Debugging on device via fastboot, recovery, or guided steps"

    def run(self, device=None, logger=None):
        if logger is None:
            logger = Logger(name="enable-debugging", log_dir=".")

        logger.info("=== Enable USB Debugging Task ===")

        # Step 1: Check if ADB already works
        logger.step(1, 5, "Checking ADB connection...")
        if self._check_adb(logger):
            logger.done("USB Debugging is already enabled. Device detected via ADB.")
            return True

        # Step 2: Check if device is in fastboot mode
        logger.step(2, 5, "Checking fastboot mode...")
        if self._check_fastboot(logger):
            logger.info("Device detected in fastboot mode.")
            logger.step(3, 5, "Attempting to enable debugging via fastboot...")
            if self._enable_via_fastboot(logger):
                logger.step(4, 5, "Rebooting device...")
                self._reboot_from_fastboot(logger)
                logger.step(5, 5, "Waiting for ADB...")
                if self._wait_for_adb(logger):
                    logger.done("USB Debugging enabled successfully via fastboot!")
                    return True
                else:
                    logger.warn("Device rebooted but ADB not detected yet.")
                    logger.info("Unlock the device and check for RSA prompt on screen.")
                    return True

        # Step 3: Check recovery mode
        logger.step(2, 5, "Checking recovery mode ADB...")
        if self._check_recovery_adb(logger):
            logger.info("Device detected in recovery with ADB!")
            logger.step(3, 5, "Enabling debugging from recovery...")
            self._enable_via_recovery_adb(logger)
            logger.step(4, 5, "Rebooting device...")
            self._reboot_via_adb(logger)
            logger.step(5, 5, "Waiting for normal ADB...")
            if self._wait_for_adb(logger):
                logger.done("USB Debugging enabled via recovery ADB!")
                return True

        # Step 4: If all automation fails, provide guided manual steps
        logger.step(2, 5, "Automation paths not available.")
        self._show_manual_guide(logger)
        return False

    def _run_cmd(self, cmd, timeout=10):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except FileNotFoundError:
            return -1, "", "Command not found"
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"

    def _check_adb(self, log):
        code, out, _ = self._run_cmd(["adb", "devices"])
        if code != 0:
            return False
        for line in out.splitlines():
            if "\tdevice" in line:
                log.info(f"Device found: {line.strip()}")
                return True
        log.info("No devices in ADB.")
        return False

    def _check_fastboot(self, log):
        code, out, _ = self._run_cmd(["fastboot", "devices"])
        if code != 0:
            log.warn("fastboot not found in PATH.")
            return False
        for line in out.splitlines():
            if "\tfastboot" in line:
                log.info(f"Fastboot device: {line.strip()}")
                return True
        log.info("No devices in fastboot.")
        return False

    def _check_recovery_adb(self, log):
        code, out, _ = self._run_cmd(["adb", "devices"])
        if code != 0:
            return False
        for line in out.splitlines():
            if "\trecovery" in line:
                log.info(f"Recovery device: {line.strip()}")
                return True
        return False

    def _enable_via_fastboot(self, log):
        commands = [
            ["fastboot", "oem", "enable-debugging"],
            ["fastboot", "oem", "unlock"],
            ["fastboot", "flashing", "unlock"],
            ["fastboot", "oem", "adb"],
        ]
        for cmd in commands:
            code, out, err = self._run_cmd(cmd, timeout=15)
            label = " ".join(cmd[1:])
            if code == 0:
                log.info(f"  '{label}' succeeded: {out[:100]}")
                return True
            else:
                log.info(f"  '{label}' failed: {err[:60]}")
        log.error("All fastboot commands failed. Device may not support them.")
        return False

    def _enable_via_recovery_adb(self, log):
        cmds = [
            "settings put global usb_config 2",
            "settings put global development_settings_enabled 1",
            "settings put secure adb_enabled 1",
            "settings put global adb_enabled 1",
            "setprop persist.service.adb.enable 1",
        ]
        for cmd in cmds:
            code, out, err = self._run_cmd(["adb", "shell", cmd], timeout=10)
            log.info(f"  '{cmd}': {err[:60] if err else 'OK'}")

    def _reboot_from_fastboot(self, log):
        self._run_cmd(["fastboot", "reboot"], timeout=30)
        log.info("Reboot command sent. Waiting 10s for device to start...")
        time.sleep(10)

    def _reboot_via_adb(self, log):
        self._run_cmd(["adb", "reboot"], timeout=15)
        time.sleep(10)

    def _wait_for_adb(self, log, timeout=60):
        deadline = time.time() + timeout
        while time.time() < deadline:
            code, out, _ = self._run_cmd(["adb", "devices"])
            if code == 0:
                for line in out.splitlines():
                    if "\tdevice" in line:
                        return True
            time.sleep(3)
        return False

    def _show_manual_guide(self, log):
        log.info("")
        log.info("=" * 60)
        log.info("  MANUAL STEPS REQUIRED")
        log.info("=" * 60)
        log.info("")
        log.info("  Enable USB Debugging on your device:")
        log.info("")
        log.info("  1. Open Settings")
        log.info("  2. Go to 'About Phone'")
        log.info("  3. Tap 'Build Number' 7 times")
        log.info("     (You'll see 'You are now a developer!')")
        log.info("  4. Go back → 'System & Updates' → 'Developer Options'")
        log.info("  5. Enable 'USB Debugging'")
        log.info("  6. Tap 'OK' to confirm")
        log.info("  7. Connect USB cable (if not already connected)")
        log.info("  8. Check the phone screen and ACCEPT the RSA fingerprint")
        log.info("")
        log.info("  After that, run:")
        log.info("    python main.py factory-reset")
        log.info("")
        log.info("  Alternative - Boot to fastboot mode:")
        log.info("    Power off device, then hold Volume Up + Power")
        log.info("    Or run: adb reboot bootloader")
        log.info("    Then run this task again.")
        log.info("=" * 60)
