import numpy as np
import csv
from utils import load_config

# ---------------- PARAMETERS ----------------
config = load_config()
G = config["G"]
EPS = config["EPS"]
DT = config["DT"]
STEPS = config["STEPS"]
N = config["N"]
OUTPUT_FILE = config["OUTPUT_PY_SEQ"]

# ---------------- INITIALIZATION ----------------
np.random.seed(config["RANDOM_SEED"])

positions = np.random.rand(N, 3)
velocities = np.zeros((N, 3))
masses = np.ones(N)

# ---------------- FORCE COMPUTATION ----------------
def compute_forces(pos, masses):
    n = len(pos)
    forces = np.zeros((n, 3))

    for i in range(n):
        for j in range(n):
            if i == j:
                continue

            r = pos[j] - pos[i]
            dist_sqr = np.dot(r, r) + EPS**2
            inv_dist3 = 1.0 / (dist_sqr ** 1.5)

            forces[i] += G * masses[i] * masses[j] * r * inv_dist3

    return forces

# ---------------- SIMULATION ----------------
with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["iteration", "body_id", "x", "y", "z"])

    for step in range(STEPS):

        forces = compute_forces(positions, masses)

        # acceleration
        accelerations = forces / masses[:, np.newaxis]

        # Euler integration
        velocities += accelerations * DT
        positions += velocities * DT

        # write CSV
        for i in range(N):
            writer.writerow([step, i,
                             positions[i, 0],
                             positions[i, 1],
                             positions[i, 2]])

print("Sequential simulation finished.")
