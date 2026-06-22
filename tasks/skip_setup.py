import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.device import Device
from lib.logger import Logger

class SkipSetupTask:
    name = "skip-setup"
    description = "Skip the setup wizard on a freshly reset device"

    def run(self, device=None, logger=None):
        if logger is None: logger = Logger(name="skip-setup", log_dir=".")
        if device is None: device = Device(log_dir=".")

        logger.info("=== Skip Setup Wizard ===")
        device.connect()
        logger.info(f"Device: {device.width}x{device.height}")

        logger.info("Waiting for setup wizard...")
        time.sleep(5)

        logger.info("Trying fast path (direct flags)...")
        device.d.shell(["settings", "put", "global", "device_provisioned", "1"])
        device.d.shell(["settings", "put", "secure", "user_setup_complete", "1"])
        device.d.shell(["settings", "put", "global", "setup_wizard_has_run", "1"])
        time.sleep(2)

        if self._is_home(device):
            logger.info("Fast path worked! Already on home screen.")
            return True

        logger.info("Walking through setup wizard screens...")
        deadline = time.time() + 600
        step = 1
        setup_actions = [
            ("Start", device.find_and_click, ["Start"]),
            ("Continue", device.find_and_click, ["Continue"]),
            ("Skip", device.find_and_click, ["Skip"]),
            ("Not now", device.find_and_click, ["Not now"]),
            ("Accept", device.find_and_click, ["Accept"]),
            ("Agree", device.find_and_click, ["Agree"]),
            ("Next", device.find_and_click, ["Next"]),
            ("Don't copy", device.find_and_click, ["Don't copy"]),
            ("Copy", device.find_and_click, ["Copy"]),
            ("Done", device.find_and_click, ["Done"]),
            ("Get started", device.find_and_click, ["Get started"]),
            ("Set up later", device.find_and_click, ["Set up later"]),
            ("Remind me later", device.find_and_click, ["Remind me later"]),
            ("Skip anyway", device.find_and_click, ["Skip anyway"]),
        ]

        while time.time() < deadline:
            focus = device.current_focus().lower()
            if self._is_home(device):
                logger.info("Home screen detected. Setup complete!")
                device.go_home()
                return True

            acted = False
            for label, action, args in setup_actions:
                if action(*args, timeout=1):
                    logger.step(step, 99, f"Tapped '{label}'")
                    step += 1
                    acted = True
                    time.sleep(2)
                    break

            if not acted:
                logger.info(f"Unknown screen, waiting... ({focus[:60]})")
                time.sleep(5)
                step += 1

            if step > 120:
                logger.error("Too many attempts. Giving up.")
                device.screenshot("setup_timeout")
                break

        logger.info("Setup wizard navigation finished.")
        return True

    def _is_home(self, d):
        focus = d.current_focus().lower()
        return any(x in focus for x in ["launcher", "home", "desktop"])

if __name__ == "__main__":
    task = SkipSetupTask()
    d = Device(log_dir=".", serial=sys.argv[1] if len(sys.argv) > 1 else None)
    l = Logger(name="skip-setup", log_dir=".")
    task.run(device=d, logger=l)
