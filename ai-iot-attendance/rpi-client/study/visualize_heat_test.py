#!/usr/bin/env python3
"""Plot a Raspberry Pi heat-test CSV file."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover - user needs the dependency
    raise SystemExit(
        "matplotlib is required to visualize the CSV. Install it with: python -m pip install matplotlib"
    ) from exc


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


def read_csv(csv_path: Path) -> tuple[list[float], list[float], list[float], list[float], list[int]]:
    times: list[float] = []
    temps: list[float] = []
    cpus: list[float] = []
    memory: list[float] = []
    throttled: list[int] = []

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            elapsed = safe_float(row.get("elapsed_seconds"))
            temp = safe_float(row.get("temperature_c"))
            cpu = safe_float(row.get("cpu_percent"))
            mem = safe_float(row.get("memory_percent"))
            if elapsed is None:
                continue
            times.append(elapsed)
            temps.append(temp if temp is not None else float("nan"))
            cpus.append(cpu if cpu is not None else float("nan"))
            memory.append(mem if mem is not None else float("nan"))
            throttled.append(parse_throttled(row.get("throttled")))

    return times, temps, cpus, memory, throttled


def plot_summary(csv_path: Path, output_path: Path) -> None:
    times, temps, cpus, memory, throttled = read_csv(csv_path)
    if not times:
        raise SystemExit(f"No usable rows found in {csv_path}")

    fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=True)

    axes[0].plot(times, temps, color="firebrick", linewidth=2)
    axes[0].set_ylabel("Temp (C)")
    axes[0].set_title(f"Heat Test: {csv_path.name}")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(times, cpus, color="royalblue", linewidth=2)
    axes[1].set_ylabel("CPU (%)")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(times, memory, color="darkgreen", linewidth=2)
    axes[2].set_ylabel("Memory (%)")
    axes[2].grid(True, alpha=0.3)

    axes[3].bar(times, throttled, color="darkorange", width=max(1.0, len(times) * 0.01))
    axes[3].set_xlabel("Elapsed seconds")
    axes[3].set_ylabel("Throttle")
    axes[3].grid(True, alpha=0.3)

    for axis in axes:
        axis.ticklabel_format(style="plain", axis="x")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    print(f"Saved plot to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a summary graph from a heat-test CSV file.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="../heat-test.csv",
        help="Path to the heat-test CSV file. Defaults to ../heat-test.csv.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("heat_test_plot.png"),
        help="Where to save the generated chart image.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv_path).expanduser().resolve()
    if not csv_path.exists():
        raise SystemExit(f"CSV file not found: {csv_path}")

    plot_summary(csv_path, args.output)


if __name__ == "__main__":
    main()
