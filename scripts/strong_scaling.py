#!/usr/bin/env python3
"""
Eksperiment 6.1 - Jako skaliranje (Strong Scaling).
Fiksan N, menja se broj jezgara P. Svaka kombinacija se izvršava NUM_RUNS puta
(config, podrazumevano 30) radi srednje vrednosti, std i outliera.

Pokretanje iz korena: python scripts/strong_scaling.py
Izlaz: scripts/results/strong_scaling.csv, strong_scaling_raw.csv
"""

import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def run_timed(cmd, cwd=None, env=None):
    t0 = time.perf_counter()
    r = subprocess.run(cmd, cwd=cwd or str(PROJECT_ROOT), env=env, capture_output=True, text=True)
    elapsed = time.perf_counter() - t0
    if r.returncode != 0:
        print(f"Error: {' '.join(cmd)}", file=sys.stderr)
        print(r.stderr, file=sys.stderr)
    return elapsed, r.returncode


def progress_bar(current, total, width=30, label="", time_sec=None):
    """Iscrtava progress bar u jednoj liniji (konzola)."""
    if total <= 0:
        return
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    pct = 100 * current / total
    extra = f"  {time_sec:.2f}s" if time_sec is not None else ""
    line = f"\r  [{bar}] {current}/{total} ({pct:.0f}%){extra}  {label}"
    sys.stdout.write(line)
    sys.stdout.flush()
    if current >= total:
        sys.stdout.write("\n")
        sys.stdout.flush()


def stats(times, n_sigma=2.0):
    """mean, std, min, max, broj outliera (van mean ± n_sigma*std)."""
    if not times:
        return None, None, None, None, 0
    mean = statistics.mean(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0.0
    lo, hi = mean - n_sigma * stdev, mean + n_sigma * stdev
    outliers = sum(1 for t in times if t < lo or t > hi)
    return mean, stdev, min(times), max(times), outliers


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    base = load_config()
    N = base.get("N", 500)
    STEPS = base.get("STEPS", 100)
    num_runs = int(base.get("NUM_RUNS", 30))
    max_cores = base.get("MAX_CORES") or (os.cpu_count() or 4)
    num_cores_list = [2**i for i in range(0, 12) if 2**i <= max_cores]
    if num_cores_list and num_cores_list[-1] != max_cores and max_cores > 0:
        num_cores_list.append(max_cores)

    config = {**base, "N": N, "STEPS": STEPS}
    save_config(config)

    all_raw = []
    summary_rows = []

    def add_summary(lang, ver, P, times):
        if not times:
            return
        mean_t, std_t, min_t, max_t, out_t = stats(times)
        summary_rows.append({
            "language": lang, "version": ver, "P": P, "N": N, "STEPS": STEPS,
            "mean_sec": round(mean_t, 4), "std_sec": round(std_t, 4),
            "min_sec": round(min_t, 4), "max_sec": round(max_t, 4),
            "num_runs": len(times), "outlier_count": out_t,
        })
        for run_idx, t in enumerate(times, 1):
            all_raw.append({"language": lang, "version": ver, "P": P, "N": N, "STEPS": STEPS, "run": run_idx, "time_sec": round(t, 4)})

    config["NUM_PROCESSES"] = 1
    save_config(config)

    print(f"\n  Strong scaling: N={N}, STEPS={STEPS}, {num_runs} runs. Cores: {num_cores_list}\n")
    print("  ┌─────────────────────────────────────────────────────────")
    print("  │ Sequential")
    print("  ├─────────────────────────────────────────────────────────")

    py_seq_times = []
    for i in range(num_runs):
        progress_bar(i + 1, num_runs, label="Python seq", time_sec=py_seq_times[-1] if py_seq_times else None)
        t, code = run_timed([sys.executable, str(PROJECT_ROOT / "python" / "sequential.py")])
        if code != 0:
            sys.exit(1)
        py_seq_times.append(t)
        progress_bar(i + 1, num_runs, label="Python seq", time_sec=t)
    add_summary("python", "seq", 1, py_seq_times)
    print("  │   ✓ Python seq done")

    rs_seq_times = []
    for i in range(num_runs):
        progress_bar(i + 1, num_runs, label="Rust seq", time_sec=rs_seq_times[-1] if rs_seq_times else None)
        t, code = run_timed(["cargo", "run", "--release", "--quiet"], cwd=str(PROJECT_ROOT / "rust" / "sequential"))
        if code != 0:
            sys.exit(1)
        rs_seq_times.append(t)
        progress_bar(i + 1, num_runs, label="Rust seq", time_sec=t)
    add_summary("rust", "seq", 1, rs_seq_times)
    print("  │   ✓ Rust seq done")
    print("  ├─────────────────────────────────────────────────────────")
    print("  │ Parallel (by P)")
    print("  ├─────────────────────────────────────────────────────────")

    for P in num_cores_list:
        print(f"  │   P = {P}")
        config["NUM_PROCESSES"] = P
        save_config(config)

        py_par_times = []
        for i in range(num_runs):
            progress_bar(i + 1, num_runs, label=f"Python par P={P}", time_sec=py_par_times[-1] if py_par_times else None)
            t, code = run_timed([sys.executable, str(PROJECT_ROOT / "python" / "parallel.py")])
            if code != 0:
                break
            py_par_times.append(t)
            progress_bar(i + 1, num_runs, label=f"Python par P={P}", time_sec=t)
        add_summary("python", "par", P, py_par_times)
        print("  │     ✓ Python par done")

        env = os.environ.copy()
        env["RAYON_NUM_THREADS"] = str(P)
        rs_par_times = []
        for i in range(num_runs):
            progress_bar(i + 1, num_runs, label=f"Rust par P={P}", time_sec=rs_par_times[-1] if rs_par_times else None)
            t, code = run_timed(["cargo", "run", "--release", "--quiet"], cwd=str(PROJECT_ROOT / "rust" / "parallel"), env=env)
            if code != 0:
                break
            rs_par_times.append(t)
            progress_bar(i + 1, num_runs, label=f"Rust par P={P}", time_sec=t)
        add_summary("rust", "par", P, rs_par_times)
        print("  │     ✓ Rust par done")

    print("  └─────────────────────────────────────────────────────────")

    raw_path = RESULTS_DIR / "strong_scaling_raw.csv"
    with open(raw_path, "w", encoding="utf-8", newline="") as f:
        f.write("language,version,P,N,STEPS,run,time_sec\n")
        for r in all_raw:
            f.write(f"{r['language']},{r['version']},{r['P']},{r['N']},{r['STEPS']},{r['run']},{r['time_sec']}\n")

    out_csv = RESULTS_DIR / "strong_scaling.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        f.write("language,version,P,N,STEPS,mean_sec,std_sec,min_sec,max_sec,num_runs,outlier_count\n")
        for r in summary_rows:
            f.write(f"{r['language']},{r['version']},{r['P']},{r['N']},{r['STEPS']},{r['mean_sec']},{r['std_sec']},{r['min_sec']},{r['max_sec']},{r['num_runs']},{r['outlier_count']}\n")

    print(f"\n  Summary: {out_csv}")
    print(f"  Raw:    {raw_path}\n")
    save_config(base)


if __name__ == "__main__":
    main()
