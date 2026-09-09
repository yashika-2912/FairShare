#!/usr/bin/env python3
"""Serve the existing Phase 5 CSV summaries in a local Flask dashboard."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from flask import Flask, jsonify, render_template


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
SCHEDULERS = ("vanilla", "fairshare")
METRICS = (
    ("response_ticks", "Response time", "ticks", "results.csv"),
    ("wait_ticks", "Waiting time", "ticks", "results.csv"),
    ("turnaround_ticks", "Turnaround time", "ticks", "results.csv"),
    ("cpu_ticks", "CPU time", "ticks", "results.csv"),
    ("context_switches", "Context switches", "count", "results.csv"),
    ("jains_fairness_index", "Jain's Fairness Index", "index", "fairness.csv"),
)

app = Flask(__name__)


def read_rows(filename: str) -> list[dict[str, str]]:
    """Load an existing experiment CSV; never generate or modify results."""
    with (EXPERIMENTS / filename).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def mean_by_workload(rows: list[dict[str, str]], metric: str) -> tuple[list[str], dict[str, list[float | None]]]:
    buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        buckets[(row["workload"], row["scheduler"])].append(float(row[metric]))

    workloads = sorted({row["workload"] for row in rows})
    series = {
        scheduler: [
            round(sum(values) / len(values), 6) if (values := buckets[(workload, scheduler)]) else None
            for workload in workloads
        ]
        for scheduler in SCHEDULERS
    }
    return workloads, series


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/results")
def results():
    payload = {"metrics": []}
    for key, label, unit, filename in METRICS:
        workloads, series = mean_by_workload(read_rows(filename), key)
        payload["metrics"].append(
            {"key": key, "label": label, "unit": unit, "workloads": workloads, "series": series}
        )
    return jsonify(payload)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

