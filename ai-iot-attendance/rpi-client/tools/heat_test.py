"""Log Raspberry Pi thermal and system data during a long-running test."""

import argparse
import csv
import os
import re
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


STOP = False


def stop_handler(signum, frame):
    del signum, frame
    global STOP
    STOP = True


def read_cpu_times() -> tuple[int, int]:
    with Path("/proc/stat").open(encoding="utf-8") as proc_stat:
        values = proc_stat.readline().split()[1:]
    numbers = [int(value) for value in values]
    idle = numbers[3] + (numbers[4] if len(numbers) > 4 else 0)
    return sum(numbers), idle


def read_cpu_percent(previous: tuple[int, int]) -> tuple[float, tuple[int, int]]:
    current = read_cpu_times()
    total_delta = current[0] - previous[0]
    idle_delta = current[1] - previous[1]
    if total_delta <= 0:
        return 0.0, current
    return (100.0 * (total_delta - idle_delta) / total_delta), current


def read_memory_percent() -> float:
    values = {}
    with Path("/proc/meminfo").open(encoding="utf-8") as meminfo:
        for line in meminfo:
            key, value = line.split(":", 1)
            values[key] = int(value.split()[0])
    total = values["MemTotal"]
    available = values.get("MemAvailable", values["MemFree"])
    return 100.0 * (total - available) / total


def read_temperature() -> float:
    thermal_zone = Path("/sys/class/thermal/thermal_zone0/temp")
    if thermal_zone.exists():
        return int(thermal_zone.read_text(encoding="utf-8")) / 1000.0

    try:
        output = subprocess.check_output(["vcgencmd", "measure_temp"], text=True, timeout=2)
    except (FileNotFoundError, subprocess.SubprocessError):
        return -1.0
    match = re.search(r"temp=([0-9.]+)", output)
    return float(match.group(1)) if match else -1.0


def read_vcgencmd(command: str) -> str:
    try:
        return subprocess.check_output(["vcgencmd", command], text=True, timeout=2).strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        return "unavailable"


def count_attendance_processes() -> int:
    count = 0
    for process in Path("/proc").glob("[0-9]*"):
        try:
            command_line = (process / "cmdline").read_bytes().decode(errors="ignore")
        except OSError:
            continue
        if "rpi-client" in command_line and "main.py" in command_line:
            count += 1
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="heat-test.csv", help="CSV output path")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between samples")
    parser.add_argument("--duration", type=float, default=0.0, help="Test duration in seconds; 0 means until Ctrl+C")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.interval <= 0:
        raise SystemExit("--interval must be greater than zero")

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = output_path.exists() and output_path.stat().st_size > 0
    fields = [
        "timestamp_utc",
        "elapsed_seconds",
        "temperature_c",
        "cpu_percent",
        "memory_percent",
        "attendance_processes",
        "throttled",
        "arm_freq",
    ]

    previous_cpu = read_cpu_times()
    started = time.monotonic()
    with output_path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        if not file_exists:
            writer.writeheader()

        print(f"Logging Raspberry Pi data to {output_path.resolve()}")
        print("Press Ctrl+C to stop.")
        while not STOP and (args.duration <= 0 or time.monotonic() - started < args.duration):
            time.sleep(args.interval)
            cpu_percent, previous_cpu = read_cpu_percent(previous_cpu)
            row = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": round(time.monotonic() - started, 1),
                "temperature_c": round(read_temperature(), 2),
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(read_memory_percent(), 2),
                "attendance_processes": count_attendance_processes(),
                "throttled": read_vcgencmd("get_throttled"),
                "arm_freq": read_vcgencmd(" measure_clock arm".strip()),
            }
            writer.writerow(row)
            csv_file.flush()
            print(
                f"{row['elapsed_seconds']}s  {row['temperature_c']}C  "
                f"CPU {row['cpu_percent']}%  throttled={row['throttled']}"
            )

    print("Heat test log closed.")


if __name__ == "__main__":
    main()