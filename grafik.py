# grafik.py - grafik Praktikum 2 (membaca hasil/histogram.txt)
import re
import statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

waktu = {}
thread_sekarang = None
for baris in open("hasil/histogram.txt"):
    h = re.search(r"thread=(\d+)", baris)
    if h:
        thread_sekarang = int(h.group(1))
        continue
    m = re.match(r"(\w+)\s+waktu=([\d.]+)", baris)
    if m and thread_sekarang is not None:
        waktu.setdefault((m.group(1), thread_sekarang), []).append(float(m.group(2)))

versi = ["critical", "atomic", "reduction", "lokal"]
nilai = [st.median(waktu[(v, 8)]) for v in versi]

plt.figure(figsize=(6.5, 4.5))
batang = plt.bar(versi, nilai, color="#2a78d6", width=0.5)
plt.yscale("log")
for b, v in zip(batang, nilai):
    plt.text(b.get_x() + b.get_width() / 2, v * 1.15, f"{v:.3f} s", ha="center", va="bottom")
plt.ylim(0.003, 60)
plt.xlabel("Versi perbaikan")
plt.ylabel("Waktu median (detik, skala log)")
plt.title("Histogram 10^8 byte, 8 thread")
plt.grid(axis="y", which="both", alpha=0.3)
plt.tight_layout()
plt.savefig("hasil/grafik_histogram_8thread.png", dpi=200)
plt.close()

print("Selesai: hasil/grafik_histogram_8thread.png")
