# ➕ Fitur Penjumlahan Otomatis

Bot sekarang mendukung penjumlahan otomatis saat input transaksi!

## 🎯 Kenapa Fitur Ini Berguna?

Saat kasir menghitung uang cash dari berbagai denominasi, atau mencatat beberapa transaksi transfer sekaligus, mereka bisa langsung input semuanya dan bot akan menjumlahkan otomatis.

**Contoh kasus real:**

- Ada 3 transfer masuk: 100rb, 50rb, 25rb → langsung input: `/tf 100k + 50k + 25k`
- Pengeluaran untuk beberapa item: beli permen 2rb, plastik 4rb, gas 50rb → `/keluar 2k, 4k, 50k`

## 📝 Cara Penggunaan

### 1. Menggunakan Tanda Plus (+)

```bash
# Transfer/QRIS
/tf 100000 + 50000 + 25000
→ Total tercatat: Rp175.000

/tf 100k + 50k + 25k
→ Total tercatat: Rp175.000

# Modal
/modal 1jt + 500rb
→ Total tercatat: Rp1.500.000

# Cash
/cash 500k + 300k + 100rb + 50000
→ Total tercatat: Rp950.000

# Pengeluaran
/keluar 20k + 15k + 5k beli gas
→ Total: Rp40.000
→ Keterangan: "beli gas"
```

### 2. Menggunakan Koma (,)

```bash
# Transfer dengan koma
/tf 100k, 50k, 25k
→ Total tercatat: Rp175.000

# Pengeluaran
/keluar 5k, 3k, 2k untuk operasional
→ Total: Rp10.000
→ Keterangan: "untuk operasional"
```

### 3. Format Campuran

Bot pintar mengenali berbagai format sekaligus:

```bash
/tf 1jt + 500rb + 250000
→ Total: Rp1.750.000

/cash 1.000.000 + 500.000 + 250rb
→ Total: Rp1.750.000

/modal 2jt + 500k + 100rb + 50000
→ Total: Rp2.650.000
```

## 💡 Tips untuk Pengeluaran dengan Keterangan

Untuk command `/keluar`, bot akan otomatis memisahkan angka dan keterangan:

### Contoh 1: Keterangan di akhir

```bash
/keluar 2000 + 4000 + 1000 beli perlengkapan toko

Parsing:
- Amount: 2000 + 4000 + 1000 = Rp7.000
- Keterangan: "beli perlengkapan toko"
```

### Contoh 2: Format natural

```bash
/keluar 2k beli permen, 4k plastik, 1k lainnya

⚠️ PERHATIAN:
Bot akan memparsing ini sebagai:
- Amount: 2000 (hanya angka pertama)
- Keterangan: "beli permen, 4k plastik, 1k lainnya"

Untuk menjumlahkan semua, gunakan:
/keluar 2k + 4k + 1k untuk permen plastik lainnya
```

### Contoh 3: Best practice

```bash
✅ RECOMMENDED:
/keluar 10k + 5k + 3k operasional toko
→ Total: Rp18.000
→ Keterangan: "operasional toko"

✅ RECOMMENDED:
/keluar 2000 + 4000 + 1000 beli gas dan perlengkapan
→ Total: Rp7.000
→ Keterangan: "beli gas dan perlengkapan"
```

## 🧮 Cara Kerja Parsing

Bot menggunakan algoritma smart parsing:

1. **Deteksi operator:** Cek apakah ada `+` atau `,` dalam input
2. **Split by operator:** Pisahkan angka-angka
3. **Parse individual:** Parse setiap angka dengan format yang didukung (k, rb, jt, dll)
4. **Sum total:** Jumlahkan semua angka
5. **Extract keterangan:** Untuk `/keluar`, ambil kata-kata setelah angka terakhir

### Alur Detail untuk `/keluar`:

```
Input: "/keluar 2k + 4k + 1k beli perlengkapan"

Step 1: Tokenize
['2k', '+', '4k', '+', '1k', 'beli', 'perlengkapan']

Step 2: Identifikasi amount vs keterangan
Amount tokens: ['2k', '+', '4k', '+', '1k']
Keterangan tokens: ['beli', 'perlengkapan']

Step 3: Parse amount
2k = 2000
4k = 4000
1k = 1000
Total = 7000

Step 4: Build keterangan
Keterangan = "beli perlengkapan"

Result:
✅ Pengeluaran Rp7.000 tercatat.
📝 Keterangan: beli perlengkapan
```

## ⚠️ Limitasi & Edge Cases

### 1. Koma dalam keterangan

```bash
# ❌ AKAN SALAH:
/keluar 5000 beli permen, coklat, permen karet

Bot akan memparsing:
- Amount: 5000 (benar)
- Sisanya sebagai keterangan (benar)

# ✅ SOLUSI:
Gunakan kata lain selain koma:
/keluar 5000 beli permen dan coklat dan permen karet
/keluar 5000 untuk permen/coklat/permen karet
```

### 2. Angka dalam keterangan

```bash
# ⚠️ HATI-HATI:
/keluar 5k beli 10 permen

Bot bisa bingung dengan "10" dalam keterangan.

# ✅ LEBIH AMAN:
/keluar 5k beli permen sepuluh biji
/keluar 5k untuk pembelian permen
```

### 3. Format tanpa spasi

```bash
# ✅ WORK:
/tf 1k+2k+3k
→ Total: Rp6.000

# ✅ WORK:
/tf 1k + 2k + 3k
→ Total: Rp6.000

# ✅ WORK:
/tf 1k, 2k, 3k
→ Total: Rp6.000
```

## 🧪 Testing

Untuk memastikan fitur bekerja dengan baik, jalankan unit test:

```bash
python test_utils.py
```

Test akan mencakup:

- Format dasar (k, rb, jt, m)
- Penjumlahan dengan +
- Penjumlahan dengan koma
- Format campuran
- Error cases
- Real-world scenarios

## 📊 Contoh Penggunaan Harian

### Morning Setup (Pagi)

```bash
/modal 1jt + 500k
# Modal awal: Rp1.500.000
```

### Throughout Day (Sepanjang Hari)

```bash
# Transfer masuk dari customer
/tf 150k + 200k + 75k
/tf 300k + 125k

# Pengeluaran
/keluar 50k + 30k + 20k beli bahan
/keluar 100k bayar listrik
/keluar 25k + 15k untuk parkir dan makan

# Cash di laci sore hari
/cash 2jt + 500k + 250k + 100rb
```

### End of Day (Akhir Hari)

```bash
# Input omzet POS
/totalpos 3500000

# Cek status
/status
```

## 🎓 Pro Tips

1. **Untuk denominasi uang:** Gunakan penjumlahan untuk menghitung cash

   ```bash
   /cash 1jt + 500k + 200k + 100k + 50k + 20k + 10k + 5k
   ```

2. **Untuk batch transfer:** Kumpulkan transfer dalam 1 input

   ```bash
   /tf 100k + 150k + 200k + 75k
   ```

3. **Untuk tracking detail:** Pisahkan pengeluaran dengan keterangan jelas

   ```bash
   /keluar 50k + 30k + 20k untuk gas plastik dan token listrik
   ```

4. **Mix format bebas:** Jangan ragu mix format
   ```bash
   /tf 1jt + 500000 + 250k + 100rb
   # Semua valid dan akan dijumlahkan!
   ```

## 🐛 Troubleshooting

### Error: "Format angka tidak valid"

**Penyebab:** Ada typo atau format yang tidak dikenali

**Solusi:**

- Cek tidak ada spasi di dalam angka: `1 000` ❌ → `1000` ✅
- Pastikan menggunakan suffix yang benar: `4kilo` ❌ → `4k` ✅
- Periksa operator: `4k ++ 5k` ❌ → `4k + 5k` ✅

### Error: "Tidak ada angka valid yang ditemukan"

**Penyebab:** Bot tidak menemukan angka dalam input

**Solusi:**

```bash
# ❌ SALAH:
/tf + + +

# ✅ BENAR:
/tf 100k + 50k + 25k
```

### Hasil penjumlahan tidak sesuai

**Penyebab:** Mungkin ada angka yang tidak terparsing

**Solusi:** Test dengan `test_utils.py` atau coba format lain

```bash
# Jika ini tidak work:
/tf 1.000.000 + 500.000

# Coba format lain:
/tf 1jt + 500k
```

## 📝 Changelog

### v1.1.0 (Current)

- ✅ Added: Penjumlahan dengan operator `+`
- ✅ Added: Penjumlahan dengan koma `,`
- ✅ Added: Smart parsing untuk pengeluaran dengan keterangan
- ✅ Added: Support campuran format (1jt + 500k + 250rb)
- ✅ Added: Unit tests untuk parsing

### v1.0.0

- Initial release dengan format angka dasar

---

**Dibuat:** Desember 2025
**Last Updated:** Desember 2025
**Status:** ✅ Production Ready
