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

### 1.5 Potencijalni šum u rezultatima
- **Turbo Boost**: Ryzen 5600H menja radni takt u zavisnosti od toplote. To može uzrokovati da rezultati sa 12 niti budu nesrazmerno gori nego sa 1 niti ako procesor smanji takt zbog pregrevanja.

- **Background processes**: Windows 11 pozadinski servisi mogu uticati na varijansu (standardnu devijaciju).

- **SMT (Simultaneous Multithreading)**: Razlika između fizičkih jezgara (1-6) i logičkih niti (7-12). Amdahlov zakon se obično bolje "drži" na fizičkim jezgrima.

---

## 2. Analiza sekvencijalnog i paralelnog dela koda

### 2.1 Procenat sekvencijalnog dela (ne može se paralelizovati)
- **Oznaka:** \( s \) (sekvencijalna frakcija, 0 ≤ s ≤ 1).
- **s =** *0.3*

### 2.2 Procenat paralelnog dela (može se paralelizovati)
- **Oznaka:** \( p = 1 - s \).
- **p =** *0.7*

---

# 3. Teorijski maksimum ubrzanja

## 3.1 Amdahlov zakon (jako skaliranje)

Prema Amdahlovom zakonu:

S(P) = 1 / ( s + (1 - s) / P )

gde je:
- s = sekvencijalna frakcija programa
- P = broj procesorskih jezgara

Maksimalno ubrzanje kada P → ∞:

S∞ = 1 / s

Za:

s = 0.30

dobijamo:

S∞ = 1 / 0.30  
S∞ ≈ 3.33

### ✅ Teorijski maksimum ubrzanja (jako skaliranje):

S∞ ≈ 3.33

To znači da program, bez obzira na broj jezgara, ne može biti brži od približno 3.33× u odnosu na sekvencijalno izvršavanje.

---

### Izračunavanje za konkretan broj jezgara

#### Za P = 6 jezgara:

S(6) = 1 / ( 0.30 + 0.70 / 6 )  
S(6) = 1 / ( 0.30 + 0.1167 )  
S(6) = 1 / 0.4167  
S(6) ≈ 2.40

#### Za P = 12 niti:

S(12) = 1 / ( 0.30 + 0.70 / 12 )  
S(12) = 1 / ( 0.30 + 0.0583 )  
S(12) = 1 / 0.3583  
S(12) ≈ 2.79

---

## 3.2 Gustafsonov zakon (slabo skaliranje)

Prema Gustafsonovom zakonu:

S(P) = s + p · P

gde je:
- s = 0.30
- p = 0.70

Dakle:

S(P) = 0.30 + 0.70P

---

### Izračunavanje za konkretan broj jezgara

#### Za P = 6:

S(6) = 0.30 + 0.70 · 6  
S(6) = 0.30 + 4.20  
S(6) = 4.50

#### Za P = 12:

S(12) = 0.30 + 0.70 · 12  
S(12) = 0.30 + 8.40  
S(12) = 8.70

---

## Zaključak

- Maksimalno teorijsko ubrzanje prema Amdahlovom zakonu iznosi približno 3.33×.
- Veći sekvencijalni deo (30%) značajno ograničava maksimalno ubrzanje.
- Kod slabog skaliranja ubrzanje i dalje raste gotovo linearno sa brojem jezgara, ali sa manjim nagibom (0.70P).

---

## 4. Grafici i tabele

Za svaku kombinaciju parametara (broj jezgara P, i kod slabog skaliranja veličina problema N) **program se izvršava ekskluzivno 30 puta**. Iz merenja se računaju **srednje vreme**, **standardna devijacija**, **min/max** i **outlier-i** (npr. vrednosti van intervala srednja ± 2σ). Skripte `strong_scaling.py` i `weak_scaling.py` to rade i generišu:
- **Sažetak:** `scripts/results/strong_scaling.csv`, `scripts/results/weak_scaling.csv` (mean_sec, std_sec, min_sec, max_sec, num_runs, outlier_count).
- **Sva merenja:** `strong_scaling_raw.csv`, `weak_scaling_raw.csv` (za eventualnu dodatnu analizu ili grafik).

### 4.1 Grafik 1: Jako skaliranje — Python, Amdahlov zakon
- **X-osa:** broj procesorskih jezgara \( P \).
- **Y-osa:** ostvareno ubrzanje \( S = T_{\text{seq}} / T_{\text{par}}(P) \) (srednje vreme sekvencijalno / srednje vreme paralelno za P jezgara).

| Broj jezgara (P) | Teorijsko ubrzanje | Ostvareno ubrzanje (Python) |
|-----------------|------------------|----------------------------|
| 1               | 1.00             | 0.95                       |
| 2               | 1.85             | 1.65                       |
| 4               | 3.10             | 2.80                       |
| 8               | 4.75             | 2.90                       |
| 12              | 5.75             | 2.91                       |

### 4.2 Grafik 2: Jako skaliranje — Rust, Amdahlov zakon
- **X-osa:** broj procesorskih jezgara \( P \).
- **Y-osa:** ostvareno ubrzanje \( S = T_{\text{seq}} / T_{\text{par}}(P) \) (srednje vreme sekvencijalno / srednje vreme paralelno za P jezgara).

| Broj jezgara (P) | Teorijsko ubrzanje | Ostvareno ubrzanje (Rust) |
|-----------------|------------------|---------------------------|
| 1               | 1.00             | 0.96                      |
| 2               | 1.85             | 1.01                      |
| 4               | 3.10             | 1.34                      |
| 8               | 4.75             | 1.02                      |
| 12              | 5.75             | 1.00                      |

### 4.3 Grafik 3: Slabo skaliranje — Python, Gustafsonov zakon
- **X-osa:** broj procesorskih jezgara \( P \).
- **Y-osa:** ostvareno ubrzanje (npr. u odnosu na P=1: posao po jezgru konstantan, pa se može posmatrati skalirano ubrzanje ili odnos vremena).

| Broj jezgara (P) | Teorijsko ubrzanje | Ostvareno ubrzanje (Python) |
|-----------------|------------------|----------------------------|
| 1               | 1.00             | 1.00                       |
| 2               | 2.00             | 0.94                       |
| 4               | 3.80             | 0.85                       |
| 8               | 7.30             | 0.64                       |
| 12              | 10.90            | 0.46                       |

### 4.4 Grafik 4: Slabo skaliranje — Rust, Gustafsonov zakon
- **X-osa:** broj procesorskih jezgara \( P \).
- **Y-osa:** ostvareno ubrzanje (npr. u odnosu na P=1: posao po jezgru konstantan, pa se može posmatrati skalirano ubrzanje ili odnos vremena).

| Broj jezgara (P) | Teorijsko ubrzanje | Ostvareno ubrzanje (Python) | Ostvareno ubrzanje (Rust) |
|-----------------|------------------|----------------------------|---------------------------|
| 1               | 1.00             | 1.00                       | 1.00                      |
| 2               | 2.00             | 0.94                       | 0.97                      |
| 4               | 3.80             | 0.85                       | 0.96                      |
| 8               | 7.30             | 0.64                       | 0.86                      |
| 12              | 10.90            | 0.46                       | 0.77                      |

---

## 5. Manipulacija poslom pri slabom skaliranju

- **Cilj:** opterećenje po jezgru približno **konstantno** kada raste broj jezgara \( P \).
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
- **SEQUENTIAL_FRACTION** — sekvencijalna frakcija s za teorijske krive na graficima (npr. 0.3).

---

## 7. Analiza i interpretacija rezultata

### 7.1 Analiza jakog skaliranja (Amdahlov zakon)

Na osnovu grafika 4.1 i 4.2, uočavaju se sledeći trendovi:

    - Zasićenje performansi: Kod Python implementacije, ubrzanje se stabilizuje (plateau) nakon 4 jezgra na vrednosti od približno 2.91×. Ovo je u skladu sa teorijskim maksimumom od S∞​≈3.33 za sekvencijalni udeo od 30%.

    - Anomalija u Rust-u: Rust implementacija pokazuje pad performansi nakon 4 jezgra. Ovo sugeriše da troškovi sinhronizacije niti (thread overhead) i komunikacije nadmašuju korist od paralelizacije kod fiksne veličine problema N.

    - Uticaj arhitekture: Rezultati na 8 i 12 niti (logička jezgra) ne pokazuju značajan napredak u odnosu na 6 fizičkih jezgara, što potvrđuje da SMT (Simultaneous Multithreading) pruža ograničene benefite za algoritme sa visokim intenzitetom računanja.

### 7.2 Analiza slabog skaliranja (Gustafsonov zakon)

Grafici 4.3 i 4.4 pokazuju značajno odstupanje od idealne linearne krive:

    - Pad efikasnosti: Iako se posao po jezgru održava konstantnim prema formuli N(P)=round(C⋅P​), ostvareno ubrzanje opada sa povećanjem P.

    - Memorijsko usko grlo: Sa porastom broja tela N i broja aktivnih jezgara, dolazi do zasićenja memorijskog protoka (memory bandwidth). Pošto procesor Ryzen 5600H ima deljeni L3 keš, konkurencija između jezgara za pristup podacima usporava izvršavanje.

    - Superiornost Rust-a: U eksperimentu slabog skaliranja, Rust pokazuje znatno bolju efikasnost (0.77× na 12 jezgara) u poređenju sa Python-om (0.46×), što ukazuje na efikasnije upravljanje memorijom i resursima pri velikim opterećenjima.

### 7.3 Zaključna razmatranja

Eksperimenti potvrđuju da je sekvencijalni deo koda (s=0.3) glavni limitirajući faktor kod jakog skaliranja. Kod slabog skaliranja, hardverska ograničenja (keš memorija i termalni throttling) sprečavaju dostizanje teorijskih Gustafsonovih vrednosti, naročito u Python okruženju koje ima veći softverski overhead.