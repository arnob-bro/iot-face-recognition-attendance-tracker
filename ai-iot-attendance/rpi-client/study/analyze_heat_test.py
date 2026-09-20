#!/usr/bin/env python3
"""Summarize a Raspberry Pi heat-test CSV file."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean


def safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value or value.lower() == "unavailable":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def safe_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value or value.lower() == "unavailable":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_throttled(value: str | None) -> int:
    if value is None:
        return 0
    value = value.strip()
    if not value or value.lower() == "unavailable":
        return 0
    try:
        return int(value, 16)
    except ValueError:
        try:
            return int(value)
        except ValueError:
            return 0


def read_rows(csv_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            temp = safe_float(row.get("temperature_c"))
            cpu = safe_float(row.get("cpu_percent"))
            mem = safe_float(row.get("memory_percent"))
            attendance = safe_int(row.get("attendance_processes"))
            throttled = parse_throttled(row.get("throttled"))
            rows.append(
                {
                    "timestamp_utc": row.get("timestamp_utc"),
                    "elapsed_seconds": safe_float(row.get("elapsed_seconds")),
                    "temperature_c": temp,
                    "cpu_percent": cpu,
                    "memory_percent": mem,
                    "attendance_processes": attendance,
                    "throttled": throttled,
                }
            )
    return rows


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    temps = [float(r["temperature_c"]) for r in rows if r["temperature_c"] is not None]
    cpus = [float(r["cpu_percent"]) for r in rows if r["cpu_percent"] is not None]
    mems = [float(r["memory_percent"]) for r in rows if r["memory_percent"] is not None]
    elapsed = [float(r["elapsed_seconds"]) for r in rows if r["elapsed_seconds"] is not None]
    attendance_values = [int(r["attendance_processes"]) for r in rows if r["attendance_processes"] is not None]
    throttled_samples = [int(r["throttled"]) for r in rows if int(r["throttled"]) > 0]

    max_temp = max(temps) if temps else 0.0
    avg_temp = mean(temps) if temps else 0.0
    max_cpu = max(cpus) if cpus else 0.0
    avg_cpu = mean(cpus) if cpus else 0.0
    max_mem = max(mems) if mems else 0.0
    avg_mem = mean(mems) if mems else 0.0
    max_attendance = max(attendance_values) if attendance_values else 0
    total_duration = max(elapsed) if elapsed else 0.0

    warnings: list[str] = []
    if max_temp >= 80:
        warnings.append("Peak temperature reached 80C or higher.")
    if max_temp >= 75:
        warnings.append("Temperature stayed high enough to cause concern for sustained operation.")
    if max_cpu >= 80:
        warnings.append("CPU usage reached 80% or higher.")
    if throttled_samples:
        warnings.append(f"Throttling was detected {len(throttled_samples)} times.")
    if max_attendance > 1:
        warnings.append("More than one attendance process instance was running at once.")

    return {
        "records": len(rows),
        "duration_seconds": round(total_duration, 2),
        "average_temperature_c": round(avg_temp, 2),
        "max_temperature_c": round(max_temp, 2),
        "average_cpu_percent": round(avg_cpu, 2),
        "max_cpu_percent": round(max_cpu, 2),
        "average_memory_percent": round(avg_mem, 2),
        "max_memory_percent": round(max_mem, 2),
        "max_attendance_processes": max_attendance,
        "throttled_samples": len(throttled_samples),
        "warnings": warnings,
    }


def print_summary(summary: dict[str, object]) -> None:
    print("Heat test summary")
    print("=" * 20)
    print(f"Records: {summary['records']}")
    print(f"Duration: {summary['duration_seconds']} s")
    print(f"Avg temp: {summary['average_temperature_c']} C")
    print(f"Max temp: {summary['max_temperature_c']} C")
    print(f"Avg CPU: {summary['average_cpu_percent']} %")
    print(f"Max CPU: {summary['max_cpu_percent']} %")
    print(f"Avg memory: {summary['average_memory_percent']} %")
    print(f"Max memory: {summary['max_memory_percent']} %")
    print(f"Max attendance processes: {summary['max_attendance_processes']}")
    print(f"Throttled samples: {summary['throttled_samples']}")

    if summary["warnings"]:
        print("\nWarnings:")
        for warning in summary["warnings"]:
            print(f"- {warning}")
    else:
        print("\nNo major warnings detected.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize Raspberry Pi heat-test CSV data.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="../heat-test.csv",
        help="Path to the heat-test CSV file. Defaults to ../heat-test.csv.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the summary as JSON instead of formatted text.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file to save the summary JSON to.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv_path).expanduser().resolve()
    if not csv_path.exists():
        raise SystemExit(f"CSV file not found: {csv_path}")

    rows = read_rows(csv_path)
    if not rows:
        raise SystemExit(f"No rows found in {csv_path}")

    summary = summarize(rows)

    if args.json:
        payload = json.dumps(summary, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload + "\n", encoding="utf-8")
        print(payload)
    else:
        print_summary(summary)


if __name__ == "__main__":
    main()
