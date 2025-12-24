# Bot Telegram Pencatatan Keuangan Toko

Bot untuk mencatat dan mengelola keuangan harian toko dengan perhitungan otomatis, rekap harian, dan **OCR otomatis via Google Gemini AI**.

## 📁 Struktur File

```
toko-bot/
├── bot.py                  # Entry point utama bot
├── config.py              # Konfigurasi & environment variables
├── storage.py             # Layer penyimpanan (SQLite)
├── logic.py               # Business logic perhitungan
├── utils.py               # Helper functions (parse, format)
├── ocr_gemini.py          # Modul OCR dengan Google Gemini AI
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (buat sendiri)
├── .env.example          # Template .env
└── toko_keuangan.db      # Database SQLite (auto-generated)
```

## 🚀 Cara Menjalankan

### 1. Persiapan

**Buat bot di Telegram:**

1. Buka [@BotFather](https://t.me/BotFather) di Telegram
2. Ketik `/newbot` dan ikuti instruksi
3. Simpan **Bot Token** yang diberikan

**Dapatkan Gemini API Key (untuk fitur OCR):**

1. Buka [Google AI Studio](https://aistudio.google.com/apikey)
2. Buat API Key baru
3. Simpan API Key untuk digunakan nanti

**Clone/Download kode:**

```bash
# Buat folder project
mkdir toko-bot
cd toko-bot

# Copy semua file Python ke folder ini
```

### 2. Setup Environment

**Install Python 3.10+:**

```bash
python --version  # pastikan >= 3.10
```

**Buat virtual environment (recommended):**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

### 3. Konfigurasi

**Buat file `.env`:**

```bash
# Copy dari template
cp .env.example .env

# Edit .env dan isi TELEGRAM_BOT_TOKEN dan GEMINI_API_KEY
nano .env  # atau text editor lain
```

**Isi di `.env`:**

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
```

### 4. Jalankan Bot

```bash
python bot.py
```

Jika berhasil, akan muncul log:

```
INFO - Database initialized at toko_keuangan.db
INFO - GeminiClient initialized successfully
INFO - Bot started...
```

**Bot siap digunakan!** Buka bot di Telegram dan ketik `/start`

### 5. Testing di Telegram

1. Buka bot Anda di Telegram
2. Tambahkan bot ke grup toko (atau chat private)
3. Test command:

```
/start
/modal 500000
/cash 1200000
/tf 800000
/keluar 50000 beli gas
/totalpos 1782000
/status
/lihat
```

4. **✨ Test fitur OCR (NEW):**

Kirim foto bukti transfer/QRIS ke bot. Bot akan otomatis:
- Menganalisa gambar dengan AI
- Mendeteksi apakah ini bukti transfer
- Mengekstrak nominal
- Menyimpan sebagai transaksi TF

## 📱 Command yang Tersedia

| Command                  | Fungsi                        | Contoh                   |
| ------------------------ | ----------------------------- | ------------------------ |
| `/modal <jumlah>`        | Catat modal awal hari ini     | `/modal 500rb`           |
| `/cash <jumlah>`         | Catat cash akhir di laci      | `/cash 1.2jt`            |
| `/tf <jumlah>`           | Catat transfer/QRIS masuk     | `/tf 800k`               |
| `/keluar <jumlah> [ket]` | Catat pengeluaran             | `/keluar 50k beli gas`   |
| `/totalpos <jumlah>`     | Input omzet POS               | `/totalpos 2.1jt`        |
| `/status`                | Lihat rekap & status hari ini | `/status`                |
| `/lihat`                 | Lihat daftar transaksi        | `/lihat`                 |
| `/edit [ID]`             | Edit/hapus transaksi          | `/edit` atau `/edit 123` |
| `/reset`                 | Reset transaksi hari ini      | `/reset`                 |
| 📷 **Kirim Foto**        | OCR otomatis via Gemini AI    | Kirim foto struk transfer |

### 📷 Fitur OCR Otomatis (NEW!)

Cukup kirim foto bukti transfer ke bot, dan AI akan:

1. **Menganalisa gambar** - Mendeteksi apakah ini bukti transfer/QRIS
2. **Mengekstrak nominal** - Membaca jumlah transfer dari gambar
3. **Menyimpan otomatis** - Data tersimpan sebagai transaksi TF
4. **Konfirmasi** - Bot mengirim pesan konfirmasi dengan detail

**Contoh response sukses:**
```
✅ TRANSFER TERDETEKSI

💰 Nominal: Rp125.000
📝 Catatan: QRIS payment detected
🤖 Confidence: 95%

Data berhasil disimpan sebagai transaksi TF hari ini.
```

**Jika gambar tidak jelas:**
```
⚠️ OCR TIDAK YAKIN

Analisa AI: Gambar buram, tidak terlihat nominal

Silakan input manual dengan:
/tf <jumlah>
```

### 🔧 Cara Menggunakan `/edit`

Command `/edit` memiliki beberapa mode:

**1. Tampilkan daftar transaksi:**

```bash
/edit
# Menampilkan 10 transaksi terbaru dengan ID-nya
```

**2. Lihat detail transaksi:**

```bash
/edit 123
# Menampilkan detail transaksi dengan ID 123
```

**3. Hapus transaksi:**

```bash
/edit 123 hapus
# Menghapus transaksi dengan ID 123
```

**4. Ubah jumlah:**

```bash
/edit 123 150k
# Mengubah jumlah transaksi ID 123 menjadi 150.000
```

**5. Ubah keterangan (untuk pengeluaran):**

```bash
/edit 123 ket beli gas dan token listrik
# Mengubah keterangan transaksi ID 123
```

### ⚠️ Validasi Input

Bot akan **TIDAK menyimpan** data jika format salah:

```bash
# ❌ Format salah - TIDAK tersimpan
/tf abcdef
→ Bot: "❌ Format tidak valid. Data TIDAK tersimpan."

# ✅ Format benar - Tersimpan
/tf 100k
→ Bot: "✅ Transfer/QRIS Rp100.000 tercatat"
```

Ini mencegah data duplikat saat user salah ketik dan input ulang.

## 💰 Format Angka yang Didukung

Bot mendukung berbagai format input:

### Format Dasar:

- `4000` - angka biasa
- `4k` atau `4K` - ribu
- `4rb`, `4 ribu` - ribu
- `4.000`, `4,000` - dengan separator
- `4jt`, `4 juta` - juta
- `4m`, `4M` - juta (million)

### Format Penjumlahan:

Bot bisa menjumlahkan beberapa angka sekaligus:

**Dengan tanda plus (+):**

```
/tf 2000 + 7000 + 8rb
/cash 500k + 300rb + 50000
/modal 1jt + 500rb
```

**Dengan koma (,):**

```
/tf 2000, 7000, 8rb
/keluar 5000, 3rb, 2000
```

**Untuk pengeluaran dengan keterangan:**

```
/keluar 2000 beli permen, 4000 plastik
# Bot akan parsing: 2000 + 4000 = 6000
# Keterangan: "beli permen, 4000 plastik"

/keluar 5k + 3k + 2rb untuk operasional toko
# Total: 10.000
# Keterangan: "untuk operasional toko"
```

## 🧮 Rumus Perhitungan

Bot menggunakan rumus fixed yang **TIDAK BOLEH diubah**:

### Definisi Variabel (per hari):

- **modal** = modal awal (input terakhir)
- **totalCash** = cash akhir di laci (input terakhir)
- **totalPengeluaran** = SUM semua pengeluaran
- **totalTF** = SUM semua transfer/QRIS
- **posTotal** = omzet POS (input terakhir)

### Perhitungan:

1. **Penjualan Cash Manual:**

   ```
   S_cash = totalCash - modal + totalPengeluaran
   ```

2. **Omzet Manual:**

   ```
   omzetManual = S_cash + totalTF
              = totalCash - modal + totalPengeluaran + totalTF
   ```

3. **Selisih:**

   ```
   selisih = omzetManual - posTotal
   selisihAbs = |selisih|
   selisihPersen = (selisihAbs / posTotal × 100) jika posTotal > 0
   ```

4. **Status:**
   - `posTotal == 0` → ⚠️ **POS BELUM INPUT**
   - `selisihAbs > 5000` → 🚨 **SELISIH BESAR**
   - `selisihAbs > 1000` → ⚠️ **SELISIH KECIL**
   - Lainnya → ✅ **COCOK**

## 🗄️ Database

Bot menggunakan **SQLite** dengan struktur:

### Tabel `transactions`:

```sql
- id (PRIMARY KEY)
- tanggal (YYYY-MM-DD)
- waktu (HH:MM:SS)
- tipe (modal/cash/tf/keluar/pos)
- jumlah (REAL)
- sumber (manual/ocr_gemini)
- keterangan (TEXT)
- chat_id, user_id, message_id
- file_id (untuk foto)
- created_at (TIMESTAMP)
```

**Backup database:**

```bash
# Copy file database
cp toko_keuangan.db backup_$(date +%Y%m%d).db
```

## 🔧 Konfigurasi Lanjutan

Edit file `.env` untuk mengubah:

```env
# Threshold selisih (Rupiah)
THRESHOLD_SELISIH_KECIL=1000
THRESHOLD_SELISIH_BESAR=5000

# Path database custom
DB_PATH=/path/to/custom.db

# Gemini API Key (WAJIB untuk OCR)
GEMINI_API_KEY=AIzaSy...
```

## 🤖 Integrasi OCR dengan Gemini AI

Bot menggunakan **Google Gemini 2.0 Flash** untuk OCR otomatis:

### Cara Kerja:

1. User kirim foto ke bot
2. Bot download foto dari Telegram
3. Bot kirim ke Gemini API untuk analisis
4. Gemini mengembalikan JSON terstruktur:
   ```json
   {
     "is_transfer": true,
     "amount": 125000,
     "confidence": 0.95,
     "reason": "QRIS payment detected"
   }
   ```
5. Bot menyimpan transaksi jika valid
6. Bot kirim konfirmasi ke user

### Yang Bisa Dideteksi:

- ✅ Screenshot transfer m-banking
- ✅ Bukti pembayaran QRIS
- ✅ Struk transfer antar bank
- ✅ Notifikasi pembayaran

### Yang TIDAK Dideteksi:

- ❌ Foto yang buram/tidak jelas
- ❌ Screenshot chat biasa
- ❌ Foto produk/selfie

## 🐛 Troubleshooting

### Bot tidak merespon:

1. Cek token bot sudah benar di `.env`
2. Pastikan bot sudah di-add ke grup
3. Cek log error di console

### OCR tidak berjalan:

1. Cek `GEMINI_API_KEY` sudah diisi di `.env`
2. Pastikan API key valid (test di Google AI Studio)
3. Cek log: `GeminiClient initialized successfully`

### Database error:

```bash
# Hapus database dan mulai fresh
rm toko_keuangan.db
python bot.py
```

### Module not found:

```bash
# Install ulang dependencies
pip install -r requirements.txt --upgrade
```

## 📊 Contoh Output `/status`

```
📊 STATUS HARI INI
📅 Senin, 5 Desember 2025

💰 Modal Awal: Rp500.000
💵 Cash Akhir (di laci): Rp1.200.000
💳 Total TF/QRIS: Rp800.000
📤 Total Pengeluaran: Rp300.000

📈 Penjualan Cash Manual (C - M + E): Rp1.000.000
📈 Omzet Manual (C - M + E + T): Rp1.800.000

🖥️ Omzet POS: Rp1.782.000
📊 Selisih (Manual - POS): Rp18.000 (1.01%)

⚠️ SELISIH KECIL
```

## 📝 Logging

Log disimpan di console. Untuk save ke file:

Edit `bot.py`:

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```

## 🛡️ Security Notes

- **JANGAN commit** file `.env` ke Git
- **JANGAN share** bot token ke orang lain
- **JANGAN share** Gemini API key ke orang lain
- **Backup** database secara berkala
- **Batasi** akses bot hanya ke grup internal

## 📞 Support

Untuk pertanyaan atau bug report:

- Cek log di console
- Review code di file terkait
- Tambahkan logging untuk debugging

## 📜 License

Private use untuk internal toko.

---

**Dibuat:** Desember 2025
**Versi:** 2.0.0
**Status:** Production Ready dengan OCR Gemini AI ✅
