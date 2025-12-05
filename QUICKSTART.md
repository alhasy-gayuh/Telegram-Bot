# 🚀 Quick Start - Bot Keuangan Toko

Panduan setup cepat dalam 5 menit!

## 📋 Checklist Persiapan

- [ ] Python 3.10+ terinstall
- [ ] Bot Token dari @BotFather
- [ ] Text editor (VS Code, Notepad++, dll)
- [ ] Terminal/Command Prompt

## ⚡ Setup Cepat

### 1️⃣ Download & Setup (2 menit)

```bash
# Buat folder project
mkdir toko-bot
cd toko-bot

# Simpan semua file Python di folder ini
# File yang diperlukan:
# - bot.py
# - config.py
# - storage.py
# - logic.py
# - utils.py
# - requirements.txt
# - .env.example

# Buat virtual environment
python -m venv venv

# Aktifkan venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Konfigurasi (1 menit)

```bash
# Copy template .env
cp .env.example .env

# Edit .env dengan text editor
# WAJIB isi: TELEGRAM_BOT_TOKEN
```

**Isi .env minimal:**

```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
```

### 3️⃣ Jalankan Bot (1 detik)

```bash
python bot.py
```

**Output sukses:**

```
INFO - Database initialized at toko_keuangan.db
INFO - Bot started...
```

### 4️⃣ Test di Telegram (1 menit)

1. Buka bot di Telegram
2. Ketik: `/start`
3. Test transaksi:

```
/modal 500k
/cash 1.2jt
/tf 800rb
/keluar 50000 beli gas
/totalpos 2.1jt
/status
```

4. **✨ Test fitur penjumlahan (NEW):**

```
# Penjumlahan dengan +
/tf 100k + 50k + 25k
/modal 1jt + 500rb
/cash 800k + 200k + 100rb

# Penjumlahan dengan koma
/tf 100k, 50k, 25k
/keluar 5k, 3k, 2k untuk operasional

# Pengeluaran dengan keterangan
/keluar 2000 beli permen, 4000 plastik
/keluar 10k + 5k + 3k beli bahan toko
```

## ✅ Verifikasi

Bot berjalan dengan baik jika:

- ✅ Merespon command `/start`
- ✅ Bisa simpan transaksi
- ✅ `/status` menampilkan perhitungan
- ✅ File `toko_keuangan.db` terbuat

## 🎯 Next Steps

1. **Add bot ke grup toko**

   - Buka grup Telegram
   - Add bot sebagai member
   - Test command di grup

2. **Backup otomatis** (optional)

   ```bash
   # Crontab untuk backup harian
   0 2 * * * cp /path/to/toko_keuangan.db /backup/toko_$(date +\%Y\%m\%d).db
   ```

3. **Setup OCR** (future - skip dulu)
   - Nanti jika sudah butuh
   - Lihat README.md bagian OCR

## 🔥 Pro Tips

**Untuk production:**

1. Jalankan bot dengan `screen` atau `tmux`:

   ```bash
   screen -S tokobot
   python bot.py
   # Ctrl+A, D untuk detach
   ```

2. Atau gunakan systemd service:
   ```bash
   # Buat file /etc/systemd/system/tokobot.service
   sudo systemctl enable tokobot
   sudo systemctl start tokobot
   ```

**Monitoring:**

```bash
# Lihat log real-time
tail -f bot.log

# Cek database size
ls -lh toko_keuangan.db
```

## ❓ FAQ Cepat

**Q: Bot tidak merespon di grup?**
A: Pastikan bot sudah di-add ke grup dan bisa lihat semua messages.

**Q: Error "TELEGRAM_BOT_TOKEN tidak ditemukan"?**
A: File `.env` belum dibuat atau token belum diisi.

**Q: Cara stop bot?**
A: Tekan `Ctrl+C` di terminal.

**Q: Database penuh?**
A: SQLite bisa handle jutaan record. Jangan khawatir.

**Q: Parsing angka error?**
A: Gunakan format yang didukung: `4000`, `4k`, `4rb`, `4.000`, `4jt`

## 🆘 Troubleshooting Cepat

| Problem             | Solution                            |
| ------------------- | ----------------------------------- |
| Module not found    | `pip install -r requirements.txt`   |
| Database locked     | Tutup semua connection, restart bot |
| Bot tidak start     | Cek token di `.env`                 |
| Command tidak kerja | Cek typo di command                 |

## 📞 Butuh Bantuan?

1. Cek log di console
2. Review README.md lengkap
3. Cek code comments di file Python

---

**Total setup time:** ~5 menit
**Siap produksi:** ✅ Yes
**OCR ready:** ⏳ Future (stub sudah ada)

Selamat mencoba! 🎉
