import json
import os
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
    r = subprocess.run(
        cmd,
        cwd=cwd or str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - t0
    if r.returncode != 0:
        print(f"Error: {' '.join(cmd)}", file=sys.stderr)
        print(r.stderr, file=sys.stderr)
    return elapsed, r.returncode


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    base = load_config()
    N = base.get("N", 500)
    STEPS = base.get("STEPS", 100)
    max_cores = base.get("MAX_CORES") or (os.cpu_count() or 4)
    num_cores_list = [2**i for i in range(0, 12) if 2**i <= max_cores]
    if num_cores_list and num_cores_list[-1] != max_cores and max_cores > 0:
        num_cores_list.append(max_cores)

    config = {**base, "N": N, "STEPS": STEPS}
    save_config(config)

    rows = []
    out_csv = RESULTS_DIR / f"strong_scaling.csv"
    config["NUM_PROCESSES"] = 1
    save_config(config)

    t_py_seq, code = run_timed([sys.executable, str(PROJECT_ROOT / "python" / "sequential.py")])
    if code != 0:
        sys.exit(1)
    rows.append({"language": "python", "version": "seq", "P": 1, "N": N, "STEPS": STEPS, "time_sec": round(t_py_seq, 4)})

    t_rs_seq, code = run_timed(
        ["cargo", "run", "--release", "--quiet"],
        cwd=str(PROJECT_ROOT / "rust" / "sequential"),
    )
    if code != 0:
        sys.exit(1)
    rows.append({"language": "rust", "version": "seq", "P": 1, "N": N, "STEPS": STEPS, "time_sec": round(t_rs_seq, 4)})

    for P in num_cores_list:
        print(f"  P = {P} ...")
        config["NUM_PROCESSES"] = P
        save_config(config)

        t_py_par, code = run_timed([sys.executable, str(PROJECT_ROOT / "python" / "parallel.py")])
        if code != 0:
            continue
        rows.append({"language": "python", "version": "par", "P": P, "N": N, "STEPS": STEPS, "time_sec": round(t_py_par, 4)})

        env = os.environ.copy()
        env["RAYON_NUM_THREADS"] = str(P)
        t_rs_par, code = run_timed(
            ["cargo", "run", "--release", "--quiet"],
            cwd=str(PROJECT_ROOT / "rust" / "parallel"),
            env=env,
        )
        if code != 0:
            continue
        rows.append({"language": "rust", "version": "par", "P": P, "N": N, "STEPS": STEPS, "time_sec": round(t_rs_par, 4)})

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        f.write("language,version,P,N,STEPS,time_sec\n")
        for r in rows:
            f.write(f"{r['language']},{r['version']},{r['P']},{r['N']},{r['STEPS']},{r['time_sec']}\n")

    save_config(base)


if __name__ == "__main__":
    main()
