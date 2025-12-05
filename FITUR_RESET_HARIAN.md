# 🔄 Fitur Reset Harian & Pemisahan Transaksi

## 🎯 Masalah yang Diselesaikan

**Masalah:**

- Perhitungan tercampur dengan transaksi hari sebelumnya
- Tidak ada pemisah jelas antara hari ini dan kemarin
- Sulit reset jika banyak transaksi salah

**Solusi:**
Bot sekarang punya sistem pemisahan transaksi berdasarkan tanggal dengan 3 mekanisme:

## 📅 1. Pemisahan Otomatis Berdasarkan Tanggal

**Cara Kerja:**

- Semua perhitungan `/status` HANYA mengambil data **tanggal hari ini**
- Data kemarin, minggu lalu, bulan lalu **TIDAK** tercampur
- Setiap command (`/tf`, `/cash`, dll) otomatis tersimpan dengan tanggal saat ini

**Contoh:**

```
Senin, 2 Des 2025:
/modal 500k
/tf 100k
/status → Hitung hanya transaksi 2 Des

Selasa, 3 Des 2025:
/modal 600k  (ini hari baru!)
/tf 150k
/status → Hitung hanya transaksi 3 Des
          (data 2 Des tidak tercampur)
```

## 🔔 2. Warning Saat Input Modal Kedua (Hari yang Sama)

**Skenario:**
User sudah input `/modal 500k` pagi hari, lalu siang input lagi `/modal 800k`

**Bot akan:**

1. Deteksi ada modal sebelumnya di hari yang sama
2. Tampilkan warning konfirmasi
3. Tanya apakah ingin **RESET SEMUA** transaksi hari itu

**Dialog:**

```
User: /modal 800k

Bot:
⚠️ PERINGATAN

Anda sudah input modal hari ini.
Input modal baru berarti RESET SEMUA transaksi hari ini.

💰 Modal baru: Rp800.000

Lanjutkan?
[✅ Ya, Reset Hari Ini]  [❌ Batal]
```

**Jika user klik "Ya, Reset Hari Ini":**

- ✅ Hapus SEMUA transaksi hari ini
- ✅ Simpan modal baru
- ✅ Mulai fresh dari awal

**Jika user klik "Batal":**

- ❌ Modal baru tidak disimpan
- ✅ Data lama tetap utuh

## 🗑️ 3. Command `/reset` - Reset Manual

**Fungsi:**
Hapus SEMUA transaksi hari ini secara manual

**Kapan Digunakan:**

- Salah input banyak transaksi
- Mau mulai ulang pencatatan hari ini
- Data kacau dan mau clean slate

**Cara Pakai:**

```bash
/reset
```

**Dialog:**

```
Bot:
⚠️ KONFIRMASI RESET

Anda akan menghapus SEMUA 15 transaksi hari ini:
📅 2025-12-05

⚠️ Tindakan ini tidak dapat dibatalkan!

Lanjutkan?
[✅ Ya, Reset]  [❌ Batal]
```

**Jika klik "Ya, Reset":**

```
✅ Reset berhasil!

🗑️ 15 transaksi telah dihapus
📅 2025-12-05

💡 Gunakan /modal untuk memulai transaksi baru
```

## 🔄 Alur Kerja Harian yang Direkomendasikan

### Pagi Hari (Buka Toko)

```bash
/modal 500k
→ ✅ Modal awal Rp500.000 tersimpan
→ 📅 Transaksi hari ini dimulai
```

### Sepanjang Hari

```bash
# Input transaksi normal
/tf 100k + 50k
/keluar 30k beli gas
/cash 1.2jt
/totalpos 2jt

# Cek status kapan saja
/status
→ Menampilkan perhitungan HANYA hari ini
```

### Jika Ada Kesalahan

```bash
# Kesalahan kecil: edit transaksi
/edit 123 150k

# Kesalahan besar: reset semua
/reset
→ Konfirmasi → Hapus semua → Input ulang dari /modal
```

### Keesokan Hari

```bash
# Input modal baru otomatis mulai hari baru
/modal 600k
→ Data kemarin tetap tersimpan (tidak tercampur)
→ Perhitungan hari ini mulai fresh
```

## 📊 Contoh Skenario Lengkap

### Skenario 1: Hari Normal

```
Rabu, 4 Des 2025

08:00 → /modal 500k
10:30 → /tf 100k
12:15 → /keluar 50k beli gas
14:00 → /tf 75k
16:30 → /cash 1.5jt
17:00 → /totalpos 1.8jt
17:05 → /status

Hasil /status:
📊 STATUS HARI INI
📅 Rabu, 4 Desember 2025
... (hanya data 4 Des)

Kamis, 5 Des 2025

08:00 → /modal 600k
10:00 → /status

Hasil /status:
📅 Kamis, 5 Desember 2025
💰 Modal Awal: Rp600.000
... (data 4 Des TIDAK muncul)
```

### Skenario 2: Salah Input Modal

```
Rabu, 4 Des 2025

08:00 → /modal 500k
        ✅ Tersimpan

10:00 → /tf 100k
10:30 → /keluar 50k

11:00 → /modal 800k  (EH SALAH!)

Bot:
⚠️ PERINGATAN
Anda sudah input modal hari ini.
Input modal baru berarti RESET SEMUA transaksi hari ini.
💰 Modal baru: Rp800.000
Lanjutkan?

User: Klik [❌ Batal]

Bot:
❌ Input modal dibatalkan

→ Data lama (500k, tf 100k, keluar 50k) tetap aman
```

### Skenario 3: Data Kacau, Mau Reset

```
Rabu, 4 Des 2025

... banyak transaksi salah ...

15:00 → /lihat
        → Ada 20 transaksi, banyak yang salah

15:05 → /reset

Bot:
⚠️ KONFIRMASI RESET
Anda akan menghapus SEMUA 20 transaksi hari ini
...

User: Klik [✅ Ya, Reset]

Bot:
✅ Reset berhasil!
🗑️ 20 transaksi telah dihapus

15:10 → /modal 500k
        → Mulai input ulang dari awal
```

## ⚠️ Hal Penting yang Perlu Diketahui

### 1. Data Lama Tidak Hilang

```
❓ Apakah data kemarin hilang saat input modal hari ini?

✅ TIDAK! Data setiap hari tersimpan terpisah.
   Modal hari ini TIDAK menghapus data kemarin.

   Data kemarin tetap ada di database,
   hanya tidak masuk perhitungan /status hari ini.
```

### 2. Reset Hanya untuk Hari Ini

```
❓ Apakah /reset menghapus data semua hari?

✅ TIDAK! /reset hanya hapus transaksi HARI INI.
   Data kemarin, minggu lalu, bulan lalu tetap aman.
```

### 3. Warning Saat Modal Kedua

```
❓ Kenapa ada warning saat input modal lagi?

✅ Karena input modal biasanya 1x per hari.
   Modal kedua = kemungkinan salah ATAU
                 memang mau reset hari ini.

   Bot tanya konfirmasi dulu untuk keamanan.
```

### 4. Tidak Bisa Undo Reset

```
⚠️  Setelah klik "Ya, Reset", data LANGSUNG DIHAPUS.
    Tidak ada fitur undo!

💡  Tips: Sebelum reset, screenshot dulu /lihat
    untuk backup jika perlu data lama.
```

## 🎓 Best Practices

### ✅ DO (Lakukan)

1. **Input `/modal` sekali di awal hari**

   - Menandai awal transaksi hari baru
   - Membuat pemisahan jelas

2. **Gunakan `/edit` untuk kesalahan kecil**

   - Ubah 1-2 transaksi yang salah
   - Lebih cepat dari reset

3. **Gunakan `/reset` untuk kesalahan besar**

   - Banyak transaksi salah
   - Mau mulai ulang fresh

4. **Cek `/status` di akhir hari**
   - Verifikasi semua data benar
   - Sebelum tutup toko

### ❌ DON'T (Jangan)

1. **Jangan input modal berkali-kali tanpa tujuan**

   - Bisa hapus data tidak sengaja
   - Selalu baca warning konfirmasi

2. **Jangan reset jika tidak perlu**

   - Gunakan `/edit` untuk fix kecil
   - Reset = hapus SEMUA

3. **Jangan lupa input `/modal` hari baru**
   - Tanpa modal, sulit tracking awal hari
   - Best practice: modal = penanda hari baru

## 🔍 FAQ

**Q: Bagaimana melihat data kemarin?**
A: Untuk saat ini, `/status` dan `/lihat` hanya tampilkan hari ini. Fitur histori multi-hari bisa ditambahkan nanti.

**Q: Bisa cancel setelah klik reset?**
A: Tidak. Setelah konfirmasi, langsung hapus. Jadi baca warning-nya dulu!

**Q: Modal harus input setiap hari?**
A: Sangat direkomendasikan. Modal = penanda awal hari baru dan berguna untuk perhitungan.

**Q: Kalau lupa input modal, data masih bisa tersimpan?**
A: Bisa! Tapi perhitungan mungkin tidak akurat karena modal = 0.

**Q: Reset bisa dilakukan kapan saja?**
A: Ya, kapan saja dalam hari yang sama. Tapi biasanya dilakukan jika ada banyak kesalahan.

---

**Dibuat:** Desember 2025
**Status:** ✅ Production Ready
**Fitur Terkait:** `/modal`, `/reset`, `/edit`, `/status`, `/lihat`
