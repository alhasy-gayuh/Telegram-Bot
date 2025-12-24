# 🚀 Panduan Migrasi Bot v3

Panduan untuk update bot di VPS dari versi lama ke versi baru dengan fitur:
- Edit rekap tanggal lalu
- **Tambah transaksi ke tanggal lalu** (misal lupa input POS)
- Audit log (riwayat perubahan)
- Total selisih di rekap mingguan/bulanan

---

## ⚠️ PENTING: Backup Dulu!

```bash
# Di VPS, backup database sebelum update
cd /path/to/bot
cp toko_keuangan.db toko_keuangan_backup_$(date +%Y%m%d).db
```

---

## 📁 File yang Perlu Diupdate

Kamu hanya perlu update **2 file** ini:

| File | Keterangan |
|------|------------|
| `bot.py` | Handler commands baru + navigasi updated |
| `storage.py` | Database layer + audit log |

> **JANGAN** update/hapus:
> - `toko_keuangan.db` ← Data kamu tersimpan di sini
> - `.env` ← Konfigurasi bot kamu

---

## 📝 Langkah-langkah Migrasi

### 1. Stop Bot di VPS
```bash
# Cari process bot
ps aux | grep bot.py

# Kill process (ganti PID dengan angka yang muncul)
kill PID

# Atau jika pakai systemd
sudo systemctl stop toko-bot
```

### 2. Backup Database
```bash
cp toko_keuangan.db toko_keuangan_backup.db
```

### 3. Upload File Baru
Upload file-file ini ke VPS (gunakan scp, sftp, atau FileZilla):

```bash
# Dari komputer lokal
scp bot.py user@vps-ip:/path/to/bot/
scp storage.py user@vps-ip:/path/to/bot/
```

### 4. Start Bot
```bash
# Aktifkan venv
source venv/bin/activate

# Start bot
python3 bot.py

# Atau jika pakai systemd
sudo systemctl start toko-bot
```

### 5. Verifikasi
Di Telegram:
1. Ketik `/start` → Menu harus muncul
2. Ketik `/help` → Harus ada command baru
3. Coba: Koreksi & Reset → Edit Rekap Tanggal Lalu
4. Coba: Rekap & Laporan → Rekap Mingguan (harus ada total selisih)

---

## 🔄 Auto-Migration Database

Saat bot pertama kali dijalankan, akan otomatis:
1. ✅ Membuat tabel `audit_log` baru
2. ✅ Menambah kolom `username` ke tabel `transactions`
3. ✅ Data lama **TIDAK** terpengaruh

---

## 🐛 Troubleshooting

### Error: Module not found
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Bot tidak merespon
```bash
# Cek log
tail -f nohup.out

# Atau jika pakai systemd
journalctl -u toko-bot -f
```

### Rollback jika bermasalah
```bash
# Stop bot
kill $(pgrep -f bot.py)

# Restore backup
cp toko_keuangan_backup.db toko_keuangan.db

# Upload file lama (jika ada backup)
```

---

## ✅ Checklist Migrasi

- [ ] Backup database di VPS
- [ ] Stop bot yang running
- [ ] Upload `bot.py`
- [ ] Upload `storage.py`
- [ ] Start bot
- [ ] Test command `/help`
- [ ] Test menu navigasi
- [ ] Test rekap mingguan (cek total selisih)
