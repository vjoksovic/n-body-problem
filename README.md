1. Definicija fizičkog modela

Problem n-tela se zasniva na Njutnovom zakonu univerzalne gravitacije. Za svako telo i u sistemu od n tela, postoji sila kojom ostala tela deluju na njega.

Algoritam (Direct Summation)

S obzirom na zahteve za paralelizaciju, koristićemo brute-force (all-pairs) pristup čija je složenost O(n2) po iteraciji. Ovo je idealno za HPC demonstraciju jer je računski intenzivno.

    Inicijalizacija: Postavljanje početnih pozicija, masa i brzina za n tela.

    Iterativni korak (Time-stepping):

        Izračunaj rezultujuću silu na svako telo (interakcija sa svim ostalim telima).

        Ažuriraj ubrzanje: ai​=Fi​/mi​.

        Ažuriraj brzinu i poziciju (korišćenjem Velocity Verlet ili Euler integracije).

    Čuvanje stanja: Upisivanje koordinata u datoteku.

2. Implementaciona specifikacija
2.1. Python Implementacija

    Sekvencijalna: Čista Python implementacija sa math ili numpy bibliotekom. Fokus na čitljivosti algoritma.

    Paralelna (multiprocessing): * Podela tela na grupe (chunks). Svaki proces računa nove sile i pozicije za svoj podskup tela.

        Korišćenje Pool ili Process objekata.

        Izlaz: output_python.csv (format: iteration, body_id, x, y, z).

2.2. Rust Implementacija

    Sekvencijalna: Fokus na performansama i "zero-cost" apstrakcijama.

    Paralelna (Threads):

        Korišćenje std::thread ili biblioteke Rayon za efikasnu distribuciju iteracija kroz petlje.

        Upotreba atomičnih referenci ili Arc<Mutex> (ako je neophodno) za deljenje podataka o pozicijama između niti.

        Izlaz: output_rust.csv (isti format kao Python radi lakše vizuelizacije).

3. Plan eksperimenata i skaliranje
3.1. Jaka skalabilnost (Strong Scaling)

    Fiksiran problem: n=2000 tela.

    Varijabla: Broj jezgara (1, 2, 4, 8, 12, 16...).

    Cilj: Izmeriti koliko se vreme izvršavanja smanjuje dodavanjem resursa za isti posao (Amdahlov zakon).

3.2. Slaba skalabilnost (Weak Scaling)

    Konstantno opterećenje: S obzirom na to da je složenost O(n2), posao po jezgru održavamo konstantnim tako što povećavamo broj tela n sa brojem jezgara P.

    Pravilo: Ako se broj jezgara poveća 4 puta, broj tela n treba da se poveća za faktor 4​=2, kako bi n2 (posao) pratio broj procesora (Gustafsonov zakon).

    Varijabla: Parovi (n,P) gde je n2/P≈const.

4. Analiza i Izveštaj

U izveštaju će biti definisani parametri:

    Procenat sekvencijalnog koda (s): Deo koda koji se bavi I/O operacijama (pisanje u fajl) i inicijalizacijom.

    Teorijski maksimumi:

        Amdahl: Speedup(P)=s+P1−s​1​

        Gustafson: Speedup(P)=s+P(1−s)

Statistička relevantnost

Svaka tačka na grafiku biće rezultat 30 nezavisnih merenja. | Konfiguracija (Jezgra/N) | Srednje vreme (s) | Std. Devijacija | Outliers | | :--- | :--- | :--- | :--- | | 1 Core / 1000 N | ... | ... | ... | | 4 Cores / 1000 N | ... | ... | ... |
5. Vizuelizacija (Rust)

Vizuelizacija će biti razvijena u Rust-u korišćenjem biblioteke Plotters.

    Ulaz: Podaci generisani iz Python/Rust simulacija.

    Prikaz: 2D ili 3D grafički prikaz putanja tela kroz iteracije.
