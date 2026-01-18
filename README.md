# Specifikacija projekta: Problem n-tela (HPC)

## 1. Definicija fizičkog modela

Problem n-tela zasniva se na Njutnovom zakonu univerzalne gravitacije. Svako telo u sistemu od *n* tela trpi silu kao rezultat gravitacionih interakcija sa svim ostalim telima.

Radi izbegavanja numeričkih singularnosti pri veoma malim rastojanjima, u izrazu sile koristi se **softening parametar** ( \varepsilon ).

[ \vec{F}*{ij} = G \frac{m_i m_j}{(r*{ij}^2 + \varepsilon^2)^{3/2}} \vec{r}_{ij} ]

Ukupna sila na telo *i* dobija se sumiranjem doprinosa svih ostalih tela.

---

## 2. Numerički metod

Problem se rešava iterativno metodom diskretnih vremenskih koraka (*time-stepping*).

Za integraciju kretanja koristi se **Eulerova metoda**, koja je jednostavna i dovoljna za potrebe ovog projekta. U svakom vremenskom koraku:

1. Izračunava se rezultujuća sila na svako telo.
2. Računa se ubrzanje:  ( \vec{a}_i = \vec{F}_i / m_i ).
3. Ažuriraju se brzina i pozicija tela.

---

## 3. Algoritam (Direct Summation)

Za izračunavanje sila koristi se **brute-force (all-pairs)** pristup, gde svako telo interaguje sa svim ostalim telima.

* Vremenska složenost: ( O(n^2) ) po iteraciji
* Razlog izbora: algoritam je računski intenzivan i pogodan za demonstraciju paralelizacije i skaliranja.

---

## 4. Implementacija u Python-u

### 4.1 Sekvencijalna verzija

* Implementirana u programskom jeziku Python.
* Fokus na jasnoći i korektnosti algoritma.
* Rezultat simulacije se čuva u CSV datoteku.

**Format izlaza:**
`iteration, body_id, x, y, z`

### 4.2 Paralelna verzija (multiprocessing)

* Paralelizacija se realizuje korišćenjem `multiprocessing` biblioteke.
* Skup tela deli se na podskupove (*chunks*), gde svaki proces računa sile i ažurira stanje za svoj deo tela.
* Rezultati se zapisuju u CSV datoteku istog formata kao u sekvencijalnoj verziji.

---

## 5. Implementacija u Rust-u

### 5.1 Sekvencijalna verzija

* Implementirana u programskom jeziku Rust.
* Fokus na performansama i eksplicitnoj kontroli memorije.
* Rezultat simulacije se čuva u CSV datoteku identičnog formata kao u Python implementaciji.

### 5.2 Paralelna verzija (threads)

* Paralelizacija se ostvaruje korišćenjem niti (`std::thread` ili biblioteka zasnovanih na nitima).
* Iteracije kroz tela se raspodeljuju na više niti.
* Deljeni podaci (pozicije tela) tretiraju se kao nepromenljivi u okviru jednog vremenskog koraka.
* Rezultati se zapisuju u CSV datoteku.

---

## 6. Eksperimenti skaliranja

### 6.1 Jako skaliranje (Strong Scaling)

* Broj tela je fiksan.
* Menja se broj korišćenih jezgara.
* Meri se vreme izvršavanja sekvencijalne i paralelne verzije u okviru istog programskog jezika.

### 6.2 Slabo skaliranje (Weak Scaling)

* Povećava se broj tela sa porastom broja jezgara.
* Za algoritam složenosti ( O(n^2) ), broj tela se bira tako da važi:

[ \frac{n^2}{P} \approx const ]

* Cilj je da se opterećenje po jezgru održi približno konstantnim.

---

## 7. Vizuelizacija

Vizuelizacija rezultata realizuje se u programskom jeziku Rust.

* Ulaz: CSV datoteke generisane tokom simulacije.
* Korišćenje grafičke biblioteke (npr. Plotters).
* Prikaz kretanja tela kroz iteracije (2D ili 3D prikaz putanja).

---

