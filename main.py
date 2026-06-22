#!/usr/bin/env python3
"""
Android Task Automator — CLI for running automation tasks on Android devices.

Usage:
    python main.py <task> [--serial SERIAL] [--log-dir DIR]

Available tasks:
    factory-reset    Factory reset + setup wizard skip
"""

import sys
import os
import argparse
import importlib
import pkgutil


def discover_tasks():
    tasks_dir = os.path.join(os.path.dirname(__file__), "tasks")
    sys.path.insert(0, os.path.dirname(__file__))
    tasks = {}
    for importer, modname, ispkg in pkgutil.iter_modules([tasks_dir]):
        try:
            mod = importlib.import_module(f"tasks.{modname}")
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if isinstance(attr, type) and hasattr(attr, "name") and hasattr(attr, "run"):
                    tasks[attr.name] = attr
        except Exception as e:
            print(f"  [WARN] Could not load task '{modname}': {e}")
    return tasks


def main():
    tasks = discover_tasks()

    parser = argparse.ArgumentParser(
        description="Android Task Automator - automate Android devices via ADB + uiautomator2"
    )
    parser.add_argument("task", nargs="?", help="Task to run: " + ", ".join(tasks.keys()) + " | python main.py <task> --serial SERIAL")
    parser.add_argument("--serial", help="Device serial (USB: XYZ12345, WiFi: 192.168.1.5:5555)")
    parser.add_argument("--log-dir", default=".", help="Directory for logs and screenshots")
    parser.add_argument("--list", action="store_true", help="List available tasks")

    args = parser.parse_args()

    if args.list or not args.task:
        print("\nAvailable tasks:\n")
        for name, cls in sorted(tasks.items()):
            desc = getattr(cls, "description", "No description")
            print(f"  {name:<20} {desc}")
        print()
        if not args.task:
            parser.print_help()
        return

    if args.task not in tasks:
        print(f"Unknown task: {args.task}")
        print(f"Available: {', '.join(tasks.keys())}")
        sys.exit(1)

    from lib.device import Device
    from lib.logger import Logger

    log = Logger(name=args.task, log_dir=args.log_dir)
    log.info(f"Starting task: {args.task}")

    device = Device(serial=args.serial, log_dir=args.log_dir)

    task_class = tasks[args.task]
    task = task_class()
    success = task.run(device=device, logger=log)

    log.done(f"Task {'succeeded' if success else 'FAILED'}")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
