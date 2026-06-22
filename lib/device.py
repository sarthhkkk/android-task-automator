import uiautomator2 as u2
import subprocess
import time
import os
from datetime import datetime


class Device:
    def __init__(self, serial=None, log_dir="."):
        self.serial = serial
        self.log_dir = log_dir
        self.d = None
        self.width = 1080
        self.height = 2400
        self.screenshot_dir = os.path.join(log_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def connect(self, timeout=30):
        if self.serial:
            self.d = u2.connect(self.serial)
        else:
            self.d = u2.connect()
        self.d.implicitly_wait(10)
        info = self.d.info
        self.width = info.get("displayWidth", 1080)
        self.height = info.get("displayHeight", 2400)
        return self

    def reconnect(self, timeout=120):
        serial = self.serial
        if not serial:
            result = subprocess.run(
                ["adb", "devices"], capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.splitlines():
                if "\tdevice" in line:
                    serial = line.split("\t")[0]
                    break
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if serial:
                    self.d = u2.connect(serial)
                else:
                    self.d = u2.connect()
                self.d.implicitly_wait(5)
                _ = self.d.info
                info = self.d.info
                self.width = info.get("displayWidth", 1080)
                self.height = info.get("displayHeight", 2400)
                return self
            except Exception:
                time.sleep(5)
        raise TimeoutError(f"Device did not reconnect within {timeout}s")

    def wake(self):
        self.d.screen_on()
        self.d.swipe(500, 2000, 500, 1000, 0.2)

    def dismiss_keyguard(self):
        self.d.shell(["wm", "dismiss-keyguard"])

    def dump_ui(self, path=None):
        if path is None:
            path = os.path.join(self.screenshot_dir, f"ui_dump_{datetime.now().strftime('%H%M%S')}.xml")
        xml = self.d.dump_hierarchy()
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        return path

    def screenshot(self, name=None):
        if not name:
            name = datetime.now().strftime("fail_%H%M%S")
        path = os.path.join(self.screenshot_dir, f"{name}.png")
        self.d.screenshot(path)
        return path

    def wait_for_screen(self, text=None, timeout=10):
        if text:
            return self.d(text=text).wait(timeout=timeout)
        return True

    def find_and_click(self, text=None, resource_id=None, cls=None, timeout=10):
        if text:
            el = self.d(text=text)
        elif resource_id:
            el = self.d(resourceId=resource_id)
        elif cls:
            el = self.d(className=cls)
        else:
            return False
        if el.wait(timeout=timeout):
            el.click()
            time.sleep(1.5)
            return True
        return False

    def find_and_click_all(self, texts, timeout=5):
        for t in texts:
            if self.find_and_click(text=t, timeout=timeout):
                return True
        return False

    def swipe_down(self, duration=0.3):
        self.d.swipe(self.width // 2, int(self.height * 0.8),
                     self.width // 2, int(self.height * 0.2), duration)

    def swipe_up(self, duration=0.3):
        self.d.swipe(self.width // 2, int(self.height * 0.2),
                     self.width // 2, int(self.height * 0.8), duration)

    def go_home(self):
        self.d.press("home")

    def back(self):
        self.d.press("back")

    def current_focus(self):
        try:
            return self.d.current_focus()
        except Exception:
            return ""
