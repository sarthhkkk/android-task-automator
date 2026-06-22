import sys
import os
from datetime import datetime
import json
import urllib.request


class Logger:
    def __init__(self, name="main", log_dir="."):
        self.name = name
        self.log_dir = log_dir
        self.webhook_url = os.environ.get("AUTOMATOR_DISCORD_WEBHOOK", "")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, f"{name}.log")

    def _timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write(self, level, msg):
        line = f"{self._timestamp()} [{level}] {msg}"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        try:
            print(line, file=sys.stdout, flush=True)
        except UnicodeEncodeError:
            print(line.encode("utf-8", errors="replace").decode("utf-8", errors="replace"), file=sys.stdout, flush=True)

    def info(self, msg):
        self._write("INFO", msg)

    def warn(self, msg):
        self._write("WARN", msg)

    def error(self, msg):
        self._write("ERROR", msg)

    def step(self, num, total, msg):
        self._write("STEP", f"[{num}/{total}] {msg}")

    def done(self, msg="Done."):
        self._write("DONE", msg)

    def discord(self, title, description, color=10181046):
        if not self.webhook_url:
            return
        safe = description.replace("\u2014", "--").replace("\u2013", "-")
        safe = safe.replace("\u2018", "'").replace("\u2019", "'")
        safe = safe.replace("\u201c", '"').replace("\u201d", '"')
        embed = {
            "embeds": [{
                "title": title,
                "description": safe[:4000],
                "color": color,
            }]
        }
        try:
            data = json.dumps(embed).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            self.warn(f"Discord send failed: {e}")
