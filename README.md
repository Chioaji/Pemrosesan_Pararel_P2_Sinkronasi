# Praktikum 2 - Sinkronisasi dan Deadlock (A06)

Mata kuliah Pemrosesan Paralel. Praktikum ini membuktikan race condition pada histogram, memperbaikinya dengan empat mekanisme sinkronisasi, membandingkan biayanya, serta mereproduksi dan memperbaiki deadlock.

## Lingkungan

AMD Ryzen 5 5625U (6 core fisik, 12 logis), Ubuntu di WSL2, GCC 15.2.0, opsi `-O2 -fopenmp`.

## Struktur folder

## Cara kompilasi dan menjalankan

```bash
# Histogram (argumen opsional = n, bawaan 10^8)
gcc -O2 -fopenmp src/histogram_perbaikan.c -o histogram_perbaikan
OMP_NUM_THREADS=8 ./histogram_perbaikan

# Deadlock (timeout 30 detik untuk versi yang macet)
gcc -O2 -fopenmp src/deadlock.c -o deadlock
timeout 30 ./deadlock || echo "macet atau dihentikan"
gcc -O2 -fopenmp src/deadlock_perbaikan.c -o deadlock_perbaikan
timeout 30 ./deadlock_perbaikan
```

## Penjelasan percobaan

### Bagian A - Membuktikan race condition (n = 10^8, benar = 100.000.000)

Perintah `h[data[i]]++` dijalankan sebagai baca, tambah, simpan. Jika dua thread membaca nilai bin yang sama sebelum salah satunya menyimpan, satu penambahan hilang.

- **A1 (8 thread, 5 eksekusi):**

| Eksekusi | total | Benar? |
|---|---|---|
| 1 | 98.582.389 | tidak |
| 2 | 97.082.129 | tidak |
| 3 | 97.025.635 | tidak |
| 4 | 97.023.812 | tidak |
| 5 | 96.856.143 | tidak |

Total selalu kurang dari n dan berbeda tiap eksekusi, karena penjadwalan thread tidak deterministik. Hanya ada 256 bin yang diperebutkan 8 thread, jadi tabrakan sering terjadi.

- **A2 (1 thread):** total = 100.000.000 dan benar. Hanya ada satu alur eksekusi, sehingga tidak ada interleaving.

### Bagian C - Empat perbaikan (`src/histogram_perbaikan.c`)

| Versi | Cara kerja |
|---|---|
| C1 `critical` | Hanya satu thread masuk ke bagian `h[data[i]]++` pada satu waktu. Aman tetapi semua thread antre. |
| C2 `atomic` | Satu pembaruan dilindungi instruksi atomik perangkat keras. Tanpa antrean kunci, tetapi baris cache tetap diperebutkan. |
| C3 `reduction(+:h[:BIN])` | Tiap thread mengisi salinan array sendiri, digabung otomatis di akhir (butuh OpenMP 4.5). |
| C4 lokal | Tiap thread mengisi histogram lokal, lalu digabung ke `h` dengan `atomic` (256 penambahan per thread). |

Semua versi diuji dan menghasilkan `benar=ya`.

### C5 - Pengukuran (n = 10^8, median 3 ulangan, detik)

| Versi | 1 thread | 8 thread | Speedup | Benar? |
|---|---|---|---|---|
| race | 0,036 | 0,693 | 0,052 | tidak (8 thread) |
| critical | 0,528 | 16,581 | 0,032 | ya |
| atomic | 0,235 | 0,450 | 0,522 | ya |
| reduction | 0,036 | 0,009 | 4,0 | ya |
| lokal | 0,037 | 0,009 | 4,1 | ya |

Urutan tercepat ke terlambat pada 8 thread: `reduction` sama dengan `lokal`, lalu `atomic`, lalu `critical`. `reduction` dan `lokal` tidak punya rebutan sama sekali karena tiap thread bekerja di salinannya sendiri. `atomic` murah per operasi tetapi 8 thread masih berebut baris cache yang sama. `critical` membuat semua thread antre untuk 10^8 penambahan, sehingga 8 thread malah sekitar 31 kali lebih lambat daripada 1 thread. Karena `critical` 8 thread hanya sekitar 16,5 detik, n = 10^8 dipakai untuk semua versi. Waktu `reduction` dan `lokal` pada 8 thread sekitar 9 ms, mendekati resolusi pengukuran, sehingga speedup keduanya hanya perkiraan kasar.

### Bagian D - Deadlock

Dua thread memindahkan dana A ke B dan B ke A masing-masing satu juta kali. Total saldo akhir harus 2.000.

- **D1 (`deadlock.c`):** `transfer_ab` mengunci A lalu B, sedangkan `transfer_ba` mengunci B lalu A. Thread yang satu memegang A sambil menunggu B, thread lainnya memegang B sambil menunggu A, sehingga terbentuk rantai tunggu melingkar. Hasil: 5 dari 5 eksekusi macet dan dihentikan `timeout` (`hasil/deadlock_d1.txt`).
- **D2 (`deadlock_perbaikan.c`):** `transfer_ba` diubah mengunci A lebih dulu lalu B, sama dengan `transfer_ab` (yang tidak diubah). Hasil: 5 dari 5 eksekusi selesai dengan saldo A = 1000,0, saldo B = 1000,0, total = 2000,0 (`hasil/deadlock_d2.txt`).

| Versi | Selesai | Macet | Total saldo bila selesai |
|---|---|---|---|
| Sebelum perbaikan (D1) | 0 dari 5 | 5 dari 5 | - |
| Sesudah perbaikan (D2) | 5 dari 5 | 0 dari 5 | 2.000,0 |

Deadlock tidak selalu terjadi karena ia hanya muncul bila kedua thread memegang kunci masing-masing pada saat yang bersinggungan, bergantung pada penjadwalan. Dengan satu juta iterasi, peluangnya hampir pasti. Perbaikan mematahkan syarat circular wait: dengan urutan kunci tetap, tidak ada thread yang memegang B sambil menunggu A.

## Catatan

Program hasil kompilasi (`histogram_perbaikan`, `deadlock`, `deadlock_perbaikan`) tidak ikut diunggah karena bisa dibuat ulang dengan perintah di atas.
