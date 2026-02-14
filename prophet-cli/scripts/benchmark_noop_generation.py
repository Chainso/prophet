#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List


def _run_cli(repo_root: Path, cwd: Path, *args: str) -> float:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "prophet-cli" / "src")
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-m", "prophet_cli", *args],
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    end = time.perf_counter()
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: prophet {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return end - start


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _summarize(values: List[float]) -> Dict[str, float]:
    return {
        "count": float(len(values)),
        "mean_ms": statistics.mean(values) * 1000.0,
        "median_ms": statistics.median(values) * 1000.0,
        "p95_ms": _percentile(values, 0.95) * 1000.0,
        "min_ms": min(values) * 1000.0,
        "max_ms": max(values) * 1000.0,
    }


def main() -> int:
    iterations = 10
    if len(sys.argv) > 1:
        iterations = int(sys.argv[1])
        if iterations < 1:
            raise ValueError("iterations must be >= 1")

    repo_root = Path(__file__).resolve().parents[2]
    source_ontology = repo_root / "examples" / "java" / "prophet_example_spring" / "ontology" / "local" / "main.prophet"

    with tempfile.TemporaryDirectory(prefix="prophet-benchmark-") as tmp:
        work_root = Path(tmp)
        _run_cli(repo_root, work_root, "init")

        ontology_dst = work_root / "domain" / "main.prophet"
        ontology_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_ontology, ontology_dst)

        cfg_path = work_root / "prophet.yaml"
        cfg_text = cfg_path.read_text(encoding="utf-8")
        cfg_text = cfg_text.replace(
            "ontology_file: path/to/your-ontology.prophet",
            "ontology_file: domain/main.prophet",
        )
        cfg_path.write_text(cfg_text, encoding="utf-8")

        # Warm baseline artifacts and cache.
        _run_cli(repo_root, work_root, "gen")

        gen_durations = []
        skip_durations = []
        for _ in range(iterations):
            gen_durations.append(_run_cli(repo_root, work_root, "gen"))
        for _ in range(iterations):
            skip_durations.append(_run_cli(repo_root, work_root, "gen", "--skip-unchanged"))

    gen_summary = _summarize(gen_durations)
    skip_summary = _summarize(skip_durations)
    speedup = gen_summary["mean_ms"] / skip_summary["mean_ms"] if skip_summary["mean_ms"] else 0.0

    payload = {
        "benchmark": "no_op_generation",
        "iterations": iterations,
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
        },
        "results": {
            "gen": gen_summary,
            "gen_skip_unchanged": skip_summary,
            "speedup_factor_mean": speedup,
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
