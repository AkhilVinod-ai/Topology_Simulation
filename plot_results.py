"""Plot PPM simulation accuracy curves from CSV outputs."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P_VALUES = [0.2, 0.4, 0.5, 0.6, 0.8]
X_VALUES = [10, 100, 1000]


def load_results(csv_path: str | Path) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    with Path(csv_path).open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(
                {
                    "p": float(row["p"]),
                    "x": int(float(row["x"])),
                    "node_acc": float(row["node_acc"]),
                    "edge_acc": float(row["edge_acc"]),
                }
            )
    return rows


def plot_group(rows: List[Dict[str, float]], mode: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    for x in X_VALUES:
        subset = [r for r in rows if r["x"] == x]
        subset.sort(key=lambda r: r["p"])

        p_vals = [r["p"] for r in subset]
        node_vals = [r["node_acc"] for r in subset]
        edge_vals = [r["edge_acc"] for r in subset]

        plt.figure(figsize=(7, 4.5))
        plt.plot(p_vals, node_vals, marker="o", linewidth=2, label="Node Sampling")
        plt.plot(p_vals, edge_vals, marker="s", linewidth=2, label="Edge Sampling")
        plt.xticks(P_VALUES)
        plt.ylim(0.0, 1.05)
        plt.xlabel("Marking probability p")
        plt.ylabel("Accuracy")
        plt.title(f"{mode.capitalize()} attacker experiment (x={x})")
        plt.grid(True, alpha=0.25)
        plt.legend()
        plt.tight_layout()

        out_path = out_dir / f"{mode}_x{x}.png"
        plt.savefig(out_path, dpi=150)
        plt.close()


def main() -> None:
    single_rows = load_results("results_single.csv")
    double_rows = load_results("results_double.csv")

    out_dir = Path("plots")
    plot_group(single_rows, mode="single", out_dir=out_dir)
    plot_group(double_rows, mode="double", out_dir=out_dir)

    print("Plots generated:")
    print("plots/single_x10.png")
    print("plots/single_x100.png")
    print("plots/single_x1000.png")
    print("plots/double_x10.png")
    print("plots/double_x100.png")
    print("plots/double_x1000.png")


if __name__ == "__main__":
    main()
