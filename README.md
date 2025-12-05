# Bot Telegram Pencatatan Keuangan Toko

Bot untuk mencatat dan mengelola keuangan harian toko dengan perhitungan otomatis dan rekap harian.

## 📁 Struktur File

```
toko-bot/
├── bot.py                  # Entry point utama bot
├── config.py              # Konfigurasi & environment variables
├── storage.py             # Layer penyimpanan (SQLite)
├── logic.py               # Business logic perhitungan
├── utils.py               # Helper functions (parse, format)
├── ocr_endpoint.py        # [OPTIONAL] Endpoint callback OCR
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

# Edit .env dan isi TELEGRAM_BOT_TOKEN
nano .env  # atau text editor lain
```

**Isi minimal di `.env`:**

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
```

### 4. Jalankan Bot

```bash
python bot.py
```

Jika berhasil, akan muncul log:

```
INFO - Database initialized at toko_keuangan.db
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

## 📱 Command yang Tersedia

| Command                  | Fungsi                        | Contoh                 |
| ------------------------ | ----------------------------- | ---------------------- |
| `/modal <jumlah>`        | Catat modal awal hari ini     | `/modal 500rb`         |
| `/cash <jumlah>`         | Catat cash akhir di laci      | `/cash 1.2jt`          |
| `/tf <jumlah>`           | Catat transfer/QRIS masuk     | `/tf 800000`           |
| `/keluar <jumlah> [ket]` | Catat pengeluaran             | `/keluar 50k beli gas` |
| `/totalpos <jumlah>`     | Input omzet POS               | `/totalpos 2100000`    |
| `/status`                | Lihat rekap & status hari ini | `/status`              |
| `/lihat`                 | Lihat daftar transaksi        | `/lihat`               |

## 💰 Format Angka yang Didukung

Bot mendukung berbagai format input:

- `4000` - angka biasa
- `4k` atau `4K` - ribu
- `4rb`, `4 ribu` - ribu
- `4.000`, `4,000` - dengan separator
- `4jt`, `4 juta` - juta
- `4m`, `4M` - juta (million)

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
- sumber (manual/ocr)
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

# N8N OCR URL (untuk integrasi OCR - opsional)
N8N_OCR_URL=http://localhost:5678/webhook/ocr-transfer
```

## 🤖 Integrasi OCR (Future - STUB)

Bot sudah disiapkan untuk integrasi OCR, tapi **belum diimplementasi penuh**.

### Yang Sudah Disiapkan:

1. ✅ Handler untuk foto dengan caption 'tf'
2. ✅ Skeleton fungsi `send_to_ocr_service()`
3. ✅ Callback handler untuk button konfirmasi
4. ✅ File `ocr_endpoint.py` untuk menerima hasil OCR

### Yang Perlu Dilengkapi Nanti:

- [ ] Implementasi HTTP POST ke n8n OCR service
- [ ] N8n workflow untuk OCR (Google Vision / Tesseract)
- [ ] Download file dari Telegram API
- [ ] Error handling untuk OCR gagal

### Cara Mengaktifkan OCR (Nanti):

1. **Jalankan OCR endpoint terpisah:**

   ```bash
   # Install dulu FastAPI (uncomment di requirements.txt)
   pip install fastapi uvicorn

   # Jalankan endpoint
   uvicorn ocr_endpoint:app --host 0.0.0.0 --port 8000
   ```

2. **Setup n8n workflow:**

   - Terima webhook dari Python bot
   - Proses gambar dengan OCR (Google Vision API / Tesseract)
   - Parse hasil OCR untuk detect transfer
   - Callback ke `http://your-server:8000/ocr-transfer-result`

3. **Update `.env`:**
   ```env
   N8N_OCR_URL=http://your-n8n-server:5678/webhook/ocr-transfer
   ```

## 🐛 Troubleshooting

### Bot tidak merespon:

1. Cek token bot sudah benar di `.env`
2. Pastikan bot sudah di-add ke grup
3. Cek log error di console

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

### Bot crash saat parsing angka:

- Cek format input, harus sesuai yang didukung
- Lihat log error untuk detail

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

## 🔄 Migration ke Database Lain

Storage layer sudah modular. Untuk migrate ke Google Sheets:

1. Buat class baru `GoogleSheetsStorage` yang implement method yang sama
2. Update `config.py` untuk select storage type
3. Ganti inisialisasi di `bot.py`:

   ```python
   # Dari:
   self.storage = Storage(self.config.DB_PATH)

   # Ke:
   self.storage = GoogleSheetsStorage(self.config.SHEETS_ID)
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
**Versi:** 1.0.0
**Status:** Production Ready (OCR belum aktif)
