# Izveštaj

---

## 1. Tehnički detalji sistema

### 1.1 Procesor
- **Model:** AMD Ryzen 5 5600H
- **Radni takt (base / boost):** 3.3 GHz
- **Organizacija cache memorije:** L1: 384 KB, L2: 3.0 MB, L3: 16.0 MB
- **Broj fizičkih jezgara:** 6
- **Broj logičkih jezgara (threads):** 12

### 1.2 RAM memorija
- **Tip:** DDR5
- **Količina:** 16 GB
- **Brzina / kanal:** 3200 MT/s

### 1.3 Operativni sistem
- **OS:** Windows 11 25H2 
- **Arhitektura:** x86_64

### 1.4 Softverske zavisnosti i verzije
- **Python:** 3.12.3
- **NumPy:** 2.2.6
- **Rust:** 1.91.1
- **Rayon:** 1.11
- **Serde** 1.0.228

---

## 2. Analiza sekvencijalnog i paralelnog dela koda

### 2.1 Procenat sekvencijalnog dela (ne može se paralelizovati)
- **Oznaka:** \( s \) (sekvencijalna frakcija, 0 ≤ s ≤ 1).
- **Objašnjenje:** Deo programa koji se po prirodi izvršava samo na jednom jezgru: inicijalizacija (pozicije, mase, seed), učitavanje konfiguracije, **zapis u CSV u svakom koraku** (ako je jedan fajl), agregacija rezultata po koracima (Euler – ažuriranje brzina/pozicija može zavisiti od redosleda ako se ne koristi double buffering), itd.
- **Procena za ovaj n-body kod:** *[npr. „Procena: s ≈ 0.05–0.15 zbog inicijalizacije, jednog glavnog ciklusa po koracima i zapisa CSV.“]*  
- **s =** *[uneti broj, npr. 0.10]*

### 2.2 Procenat paralelnog dela (može se paralelizovati)
- **Oznaka:** \( p = 1 - s \).
- **Objašnjenje:** Izračunavanje sila (all-pairs) dominira vremenom i lako se paralelizuje po telima; ostali delovi (Euler, zapis) su mali u odnosu na račun sila.
- **p =** *[npr. 0.90]*

---

## 3. Teorijski maksimum ubrzanja

### 3.1 Amdahlov zakon (jako skaliranje)
- **Fiksan posao**, povećava se broj jezgara \( P \).
- **Maksimalno ubrzanje (P → ∞):** \( S_{\infty} = 1/s \).
- **Za unetu vrednost s =** *[vrednost]* **→ teorijski maksimum ubrzanja:** *[npr. 1/0.10 = 10]*

*Na grafiku jako skaliranja nacrtati krivu \( S_{\text{Amdahl}}(P) \) kao „teorijski maksimum“ i uporediti sa ostvarenim ubrzanjem (vreme sekvencijalno / vreme paralelno za P jezgara).*

### 3.2 Gustafsonov zakon (slabo skaliranje)
- **Fiksno vreme** — posao raste sa P tako da vreme ostane približno konstantno.
- **Za unete vrednosti s i p:** *[npr. S(P) = 0.10 + 0.90·P]*

*Na grafiku slabog skaliranja nacrtati \( S_{\text{Gustafson}}(P) \) kao „teorijski maksimum“ i uporediti sa ostvarenim ubrzanjem (npr. posao po jezgru konstantan, meri se vreme; ubrzanje se može definisati u odnosu na referentni P=1).*

**Korisna referenca:** članak o Amdahlovom i Gustafsonovom zakonu (npr. „Amdahl's law“, „Gustafson's law“ na Wikipediji ili predmetna literatura).

---

## 4. Zahtevani grafici i potporne tabele

Za svaku kombinaciju parametara (broj jezgara P, i kod slabog skaliranja veličina problema N) **program se izvršava ekskluzivno 30 puta**. Iz merenja se računaju **srednje vreme**, **standardna devijacija**, **min/max** i **outlier-i** (npr. vrednosti van intervala srednja ± 2σ). Skripte `strong_scaling.py` i `weak_scaling.py` to rade i generišu:
- **Sažetak:** `scripts/results/strong_scaling.csv`, `scripts/results/weak_scaling.csv` (mean_sec, std_sec, min_sec, max_sec, num_runs, outlier_count).
- **Sva merenja:** `strong_scaling_raw.csv`, `weak_scaling_raw.csv` (za eventualnu dodatnu analizu ili grafik).

### 4.1 Grafik 1: Jako skaliranje — Python, Amdahlov zakon
- **X-osa:** broj procesorskih jezgara \( P \).
- **Y-osa:** ostvareno ubrzanje \( S = T_{\text{seq}} / T_{\text{par}}(P) \) (srednje vreme sekvencijalno / srednje vreme paralelno za P jezgara).
- **Linija teorijskog maksimuma:** \( S_{\text{Amdahl}}(P) \) za unetu vrednost \( s \).
- **Potporna tabela:** za svaki P: P, N, STEPS, mean_sec, std_sec, min_sec, max_sec, num_runs, outlier_count; opciono i ostvareno ubrzanje.

### 4.2 Grafik 2: Jako skaliranje — Rust, Amdahlov zakon
- Isto kao 4.1, za Rust paralelnu implementaciju.
- **Potporna tabela:** isti format kao za Python.

### 4.3 Grafik 3: Slabo skaliranje — Python, Gustafsonov zakon
- **X-osa:** broj procesorskih jezgara \( P \).
- **Y-osa:** ostvareno ubrzanje (npr. u odnosu na P=1: posao po jezgru konstantan, pa se može posmatrati skalirano ubrzanje ili odnos vremena).
- **Linija teorijskog maksimuma:** \( S_{\text{Gustafson}}(P) \).
- **Potporna tabela:** P, N, STEPS, mean_sec, std_sec, min_sec, max_sec, num_runs, outlier_count.

### 4.4 Grafik 4: Slabo skaliranje — Rust, Gustafsonov zakon
- Isto kao 4.3, za Rust.
- **Potporna tabela:** isti format.

---

## 5. Manipulacija poslom pri slabom skaliranju

- **Cilj:** opterećenje po jezgru približno **konstantno** kada raste broj jezgara \( P \).
- **Složenost po iteraciji:** \( O(n^2) \) (all-pairs sile). Ukupan „posao“ proporcionalan je \( n^2 \). Da bi posao po jezgru bio konstantan, želimo \( n^2 / P \approx \text{const} \), odnosno \( n^2 \propto P \), tj. \( n \propto \sqrt{P} \).
- **Parametri:** bira se **bazni broj tela** \( N_{\text{base}} \) za \( P = 1 \). Konstanta \( C = N_{\text{base}}^2 \). Za svaki \( P \) broj tela je \( N(P) = \text{round}(\sqrt{C \cdot P}) \), tako da \( N^2 / P \approx C \).
- **Implementacija u skripti:** u `config.json` se koristi `N_BASE_WEAK`; skripta za svaki P računa \( N \) i postavlja `N` i `NUM_PROCESSES` (odnosno broj niti) pre pokretanja. Na ovaj način **modifikacijom parametara (N i P)** postiže se konstantan posao po procesorskom jezgru.

---

## 6. Pokretanje eksperimenata i generisanje podataka

### Broj pokretanja po konfiguraciji
- U `config/config.json` postaviti **`NUM_RUNS`: 30** (ili željeni broj). Svaka kombinacija (P, N) za jako/slabo skaliranje izvršava se 30 puta; skripte računaju mean, std, min, max i outlier_count.

### Komande
```bash
python scripts/strong_scaling.py   # → results/strong_scaling.csv, strong_scaling_raw.csv
python scripts/weak_scaling.py     # → results/weak_scaling.csv, weak_scaling_raw.csv
python scripts/plot_graphs.py      # → grafike iz CSV (4.1–4.4) u results/*.png
```

### Generisanje grafika (4.1–4.4)
Skripta `plot_graphs.py` čita `scripts/results/strong_scaling.csv` i `weak_scaling.csv` i crta:
- **Grafik 1:** Jako skaliranje — Python, Amdahlov zakon → `strong_scaling_python.png`
- **Grafik 2:** Jako skaliranje — Rust, Amdahlov zakon → `strong_scaling_rust.png`
- **Grafik 3:** Slabo skaliranje — Python, Gustafsonov zakon → `weak_scaling_python.png`
- **Grafik 4:** Slabo skaliranje — Rust, Gustafsonov zakon → `weak_scaling_rust.png`

Opcije:
- `--s 0.10` — sekvencijalna frakcija za teorijske krive (ili u configu `SEQUENTIAL_FRACTION`)
- `--tables` — upisuje potporne tabele u `*_table.txt`
- `--no-plots` — samo tabele, bez grafika

Zavisnost: `pip install matplotlib`

### Opciono u configu
- **MAX_CORES** — ograničiti broj jezgara (npr. 8).
- **N_BASE_WEAK** — bazni broj tela za slabo skaliranje.
- **NUM_RUNS** — broj ponavljanja po konfiguraciji (preporuka 30).
- **SEQUENTIAL_FRACTION** — sekvencijalna frakcija s za teorijske krive na graficima (npr. 0.10).

---
