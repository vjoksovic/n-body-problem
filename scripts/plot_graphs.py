import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
GRAPHS_DIR = Path(__file__).resolve().parent / "graphs"
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path):
    """Vraća listu dict redova. Kolone kao ključevi."""
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


def amdahl_speedup(P, s):
    """Teorijsko ubrzanje po Amdahlovom zakonu: S(P) = 1 / (s + (1-s)/P)."""
    if P <= 0:
        return 0.0
    return 1.0 / (s + (1 - s) / P)


def gustafson_speedup(P, s):
    """Teorijsko ubrzanje po Gustafsonovom zakonu: S(P) = s + (1-s)*P."""
    return s + (1 - s) * P


def strong_scaling_data(rows, language):
    """Iz summary redova izvlači P i mean_sec za seq i par za dati jezik."""
    seq_mean = None
    par = []  # (P, mean_sec)
    for r in rows:
        if r.get("language") != language:
            continue
        P = int(r["P"])
        mean_sec = float(r["mean_sec"])
        if r.get("version") == "seq":
            seq_mean = mean_sec
        elif r.get("version") == "par":
            par.append((P, mean_sec))
    par.sort(key=lambda x: x[0])
    return seq_mean, par


def weak_scaling_data(rows, language):
    """Svi redovi su par; za svaki P imamo mean_sec. Ubrzanje = T(P=1)/T(P)."""
    by_p = {}  # P -> mean_sec
    for r in rows:
        if r.get("language") != language:
            continue
        P = int(r["P"])
        by_p[P] = float(r["mean_sec"])
    if not by_p:
        return None, []
    p1_time = by_p.get(1)
    if p1_time is None or p1_time <= 0:
        p1_time = min(by_p.values())
    speedups = [(P, p1_time / t) for P, t in sorted(by_p.items()) if t > 0]
    return p1_time, speedups


def plot_strong_one(ax, lang_label, seq_mean, par_data, s, title, out_path):
    import matplotlib.pyplot as plt
    import numpy as np

    fig = ax.get_figure()
    if seq_mean is None or not par_data:
        ax.text(0.5, 0.5, "Nema dovoljno podataka", ha="center", va="center", transform=ax.transAxes)
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    P_vals = [x[0] for x in par_data]
    speedups = [seq_mean / t for _, t in par_data]
    P_smooth = np.linspace(1, max(P_vals) if P_vals else 2, 200)
    amdahl_curve = [amdahl_speedup(P, s) for P in P_smooth]

    ax.plot(P_smooth, amdahl_curve, "k--", label="Amdahl (teorija)", linewidth=1.5)
    ax.plot(P_vals, speedups, "o-", label=f"{lang_label} (ostvareno)", markersize=8)
    ax.set_xlabel("Broj jezgara P")
    ax.set_ylabel("Ubrzanje S = T_seq / T_par(P)")
    ax.set_title(title)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_weak_one(ax, lang_label, speedups_data, s, title, out_path):
    import matplotlib.pyplot as plt
    import numpy as np

    fig = ax.get_figure()
    if not speedups_data:
        ax.text(0.5, 0.5, "Nema dovoljno podataka", ha="center", va="center", transform=ax.transAxes)
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    P_vals = [x[0] for x in speedups_data]
    speedups = [x[1] for x in speedups_data]
    P_smooth = np.linspace(1, max(P_vals) if P_vals else 2, 200)
    gustafson_curve = [gustafson_speedup(P, s) for P in P_smooth]

    ax.plot(P_smooth, gustafson_curve, "k--", label="Gustafson (teorija)", linewidth=1.5)
    ax.plot(P_vals, speedups, "o-", label=f"{lang_label} (ostvareno)", markersize=8)
    ax.set_xlabel("Broj jezgara P")
    ax.set_ylabel("Ubrzanje (u odnosu na P=1)")
    ax.set_title(title)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_support_table(rows, path, extra_cols=None):
    """Ispisuje potpornu tabelu u tekst fajl."""
    if not rows:
        return
    keys = list(rows[0].keys())
    if extra_cols:
        for k in extra_cols:
            if k not in keys:
                keys.append(k)
    with open(path, "w", encoding="utf-8") as f:
        w = max(len(k) for k in keys) + 2
        header = "".join(k.ljust(w) for k in keys)
        f.write(header + "\n")
        f.write("-" * len(header) + "\n")
        for r in rows:
            line = "".join(str(r.get(k, "")).ljust(w) for k in keys)
            f.write(line + "\n")


def main():
    parser = argparse.ArgumentParser(description="Grafici iz strong/weak scaling CSV")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR, help="Direktorijum sa CSV fajlovima")
    parser.add_argument("--s", type=float, default=None, help="Sekvencijalna frakcija s (0-1). Ako nije navedeno, iz config.json SEQUENTIAL_FRACTION ili 0.10")
    parser.add_argument("--tables", action="store_true", help="Upisati potporne tabele u *_table.txt")
    parser.add_argument("--no-plots", action="store_true", help="Samo tabele, bez grafika")
    args = parser.parse_args()

    config = load_config()
    s = args.s if args.s is not None else config.get("SEQUENTIAL_FRACTION", 0.10)
    if not (0 < s < 1):
        s = 0.10

    strong_path = args.results_dir / "strong_scaling.csv"
    weak_path = args.results_dir / "weak_scaling.csv"

    strong_rows = read_csv(strong_path)
    weak_rows = read_csv(weak_path)

    if not strong_rows and not weak_rows:
        print("Nema redova u strong_scaling.csv ni weak_scaling.csv. Pokrenite strong_scaling.py i weak_scaling.py.", file=sys.stderr)
        sys.exit(1)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib nije instaliran. Instalirajte: pip install matplotlib", file=sys.stderr)
        sys.exit(1)

    args.results_dir.mkdir(parents=True, exist_ok=True)

    # Strong scaling — Python
    seq_py, par_py = strong_scaling_data(strong_rows, "python")
    if not args.no_plots:
        fig, ax = plt.subplots()
        plot_strong_one(
            ax, "Python", seq_py, par_py, s,
            "Strong scaling — Python, Amdahl's law",
            GRAPHS_DIR / "strong_scaling_python.png",
        )
        print("  Recorded:", GRAPHS_DIR / "strong_scaling_python.png")

    # Strong scaling — Rust
    seq_rs, par_rs = strong_scaling_data(strong_rows, "rust")
    if not args.no_plots:
        fig, ax = plt.subplots()
        plot_strong_one(
            ax, "Rust", seq_rs, par_rs, s,
            "Strong scaling — Rust, Amdahl's law",
            GRAPHS_DIR / "strong_scaling_rust.png",
        )
        print("  Recorded:", GRAPHS_DIR / "strong_scaling_rust.png")

    # Weak scaling — Python
    _, speedups_py = weak_scaling_data(weak_rows, "python")
    if not args.no_plots:
        fig, ax = plt.subplots()
        plot_weak_one(
            ax, "Python", speedups_py, s,
            "Weak scaling — Python, Gustafson's law",
            GRAPHS_DIR / "weak_scaling_python.png",
        )
        print("  Recorded:", GRAPHS_DIR / "weak_scaling_python.png")

    # Weak scaling — Rust
    _, speedups_rs = weak_scaling_data(weak_rows, "rust")
    if not args.no_plots:
        fig, ax = plt.subplots()
        plot_weak_one(
            ax, "rust", speedups_rs, s,
            "Weak scaling — Rust, Gustafson's law",
            GRAPHS_DIR / "weak_scaling_rust.png",
        )
        print("  Recorded:", GRAPHS_DIR / "weak_scaling_rust.png")

if __name__ == "__main__":
    main()
