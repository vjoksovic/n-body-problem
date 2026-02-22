# Eksperimenti skaliranja (sekcija 6)

Skripte za merenje jako i slabog skaliranja n-body simulacije.

## Preduslov

- Python sa zavisnostima iz `python/` (numpy itd.)
- Rust toolchain; pre prvog pokretanja u `rust/sequential` i `rust/parallel`:
  ```bash
  cargo build --release --manifest-path rust/sequential/Cargo.toml
  cargo build --release --manifest-path rust/parallel/Cargo.toml
  ```
- Pokretanje **iz korena projekta** (gde je `config/` i `python/`).

## 6.1 Jako skaliranje (Strong Scaling)

**Fiksan N**, menja se broj jezgara **P**. Meri se vreme sekvencijalne i paralelne verzije (Python i Rust).

```bash
python scripts/strong_scaling.py
```

- Koristi `N` i `STEPS` iz `config/config.json`.
- Opciono u config: `MAX_CORES` (ceo broj) da ograničiš broj jezgara.
- Rezultati: `scripts/results/strong_scaling_<timestamp>.csv`  
  Kolone: `language,version,P,N,STEPS,time_sec`

## 6.2 Slabo skaliranje (Weak Scaling)

**N raste sa P** tako da **n²/P ≈ const** (opterećenje po jezgru približno konstantno).

```bash
python scripts/weak_scaling.py
```

- Za osnovu broja tela koristi `N_BASE_WEAK` iz configa (ako nema, koristi `N`).
- Za svaki P računa `N = round(sqrt(N_base² * P))`.
- Rezultati: `scripts/results/weak_scaling_<timestamp>.csv`  
  Kolone: `language,version,P,N,STEPS,time_sec`

## Konfiguracija

U `config/config.json` možeš dodati:

- `MAX_CORES` – maksimalan broj jezgara za oba eksperimenta (podrazumevano: sve dostupne).
- `N_BASE_WEAK` – osnovni broj tela za slabo skaliranje (za P=1).
