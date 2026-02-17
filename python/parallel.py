import numpy as np
import csv
import multiprocessing as mp
from utils import load_config

# ---------------- PARAMETERS ----------------
config = load_config()
G = config["G"]
EPS = config["EPS"]
DT = config["DT"]
STEPS = config["STEPS"]
N = config["N"]
OUTPUT_FILE = config["OUTPUT_PY_PAR"]
NUM_PROCESSES = config["NUM_PROCESSES"]

# ---------------- FORCE WORKER ----------------
def compute_chunk(start, end, positions, masses):
    n = len(positions)
    forces_chunk = np.zeros((end - start, 3))

    for idx, i in enumerate(range(start, end)):
        for j in range(n):
            if i == j:
                continue

            r = positions[j] - positions[i]
            dist_sqr = np.dot(r, r) + EPS**2
            inv_dist3 = 1.0 / (dist_sqr ** 1.5)

            forces_chunk[idx] += G * masses[i] * masses[j] * r * inv_dist3

    return start, forces_chunk


# ---------------- SIMULATION ----------------
if __name__ == "__main__":

    np.random.seed(config["RANDOM_SEED"])

    positions = np.random.rand(N, 3)
    velocities = np.zeros((N, 3))
    masses = np.ones(N)

    chunk_size = N // NUM_PROCESSES

    with mp.Pool(processes=NUM_PROCESSES) as pool:
        with open(OUTPUT_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["iteration", "body_id", "x", "y", "z"])

            for step in range(STEPS):

                tasks = []
                for p in range(NUM_PROCESSES):
                    start = p * chunk_size
                    end = (p + 1) * chunk_size if p != NUM_PROCESSES - 1 else N
                    tasks.append((start, end, positions, masses))

                results = pool.starmap(compute_chunk, tasks)

                forces = np.zeros((N, 3))
                for start, chunk_forces in results:
                    forces[start:start + len(chunk_forces)] = chunk_forces

                accelerations = forces / masses[:, np.newaxis]

                velocities += accelerations * DT
                positions += velocities * DT

                for i in range(N):
                    writer.writerow([step, i,
                                     positions[i, 0],
                                     positions[i, 1],
                                     positions[i, 2]])

    print("Parallel simulation finished.")
