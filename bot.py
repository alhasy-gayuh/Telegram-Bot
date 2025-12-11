"""
Telegram Bot untuk Pencatatan Keuangan Harian Toko
Entry point utama bot
"""

import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from config import Config
from storage import Storage
from logic import FinancialLogic
from utils import parse_amount, format_rupiah
from ocr_gemini import GeminiClient
from datetime import datetime

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TokoBot:
    def __init__(self):
        self.config = Config()
        self.storage = Storage(self.config.DB_PATH)
        self.logic = FinancialLogic(self.storage)
        self.gemini = GeminiClient()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk command /start"""
        welcome_message = """
🏪 *Bot Pencatatan Keuangan Toko*

📝 Perintah Input:
• /modal <jumlah> - Catat modal awal
• /cash <jumlah> - Catat cash akhir di laci
• /tf <jumlah> - Catat transfer/QRIS
• /keluar <jumlah> [ket] - Catat pengeluaran
• /totalpos <jumlah> - Input omzet POS

📊 Perintah Lihat Data:
• /status - Status keuangan hari ini
• /lihat - Daftar transaksi hari ini
• /edit - Edit transaksi yang salah
• /reset - Reset semua transaksi hari ini

💡 Format angka:
• 4000, 4k, 4rb, 4.000, 4jt
• Penjumlahan: 2k + 3k + 5k

⚠️ Tips:
• Input /modal menandai awal hari baru
• Semua perhitungan berdasarkan tanggal
• Gunakan /reset jika ada kesalahan besar
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def modal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /modal <amount>"""
        try:
            if not context.args:
                await update.message.reply_text("❌ Format: /modal <jumlah>\nContoh: /modal 500k")
                return

            amount_str = ' '.join(context.args)

            try:
                amount = parse_amount(amount_str)
            except ValueError as e:
                await update.message.reply_text(f"❌ Format tidak valid: {str(e)}\n\n✅ Data TIDAK tersimpan.")
                return

            if amount <= 0:
                await update.message.reply_text("❌ Jumlah harus > 0\n\n✅ Data TIDAK tersimpan.")
                return

            tanggal = datetime.now().strftime('%Y-%m-%d')
            waktu = datetime.now().strftime('%H:%M:%S')

            # Cek apakah sudah ada modal hari ini
            modal_exists = self.storage.check_modal_exists_today(tanggal)

            if modal_exists:
                # Kirim warning dengan pilihan
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Ya, Reset Hari Ini", callback_data=f"reset_and_modal_{amount}"),
                        InlineKeyboardButton("❌ Batal", callback_data="cancel_modal")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    f"⚠️ *PERINGATAN*\n\n"
                    f"Anda sudah input modal hari ini.\n"
                    f"Input modal baru berarti *RESET SEMUA* transaksi hari ini.\n\n"
                    f"💰 Modal baru: {format_rupiah(amount)}\n\n"
                    f"Lanjutkan?",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return

            # Simpan transaksi modal
            self.storage.add_transaction(
                tanggal=tanggal,
                waktu=waktu,
                tipe='modal',
                jumlah=amount,
                sumber='manual',
                keterangan='',
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id,
                message_id=update.message.message_id
            )

            await update.message.reply_text(
                f"✅ Modal awal {format_rupiah(amount)} tersimpan\n"
                f"📅 Transaksi hari ini dimulai"
            )
            logger.info(f"Modal saved: {amount} by user {update.effective_user.id}")

        except Exception as e:
            logger.error(f"Error in modal_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def cash_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /cash <amount>"""
        try:
            if not context.args:
                await update.message.reply_text("❌ Format: /cash <jumlah>\nContoh: /cash 1.2jt")
                return

            amount_str = ' '.join(context.args)

            try:
                amount = parse_amount(amount_str)
            except ValueError as e:
                await update.message.reply_text(f"❌ Format tidak valid: {str(e)}\n\n✅ Data TIDAK tersimpan.")
                return

            if amount < 0:
                await update.message.reply_text("❌ Jumlah tidak boleh negatif\n\n✅ Data TIDAK tersimpan.")
                return

            tanggal = datetime.now().strftime('%Y-%m-%d')
            waktu = datetime.now().strftime('%H:%M:%S')

            self.storage.add_transaction(
                tanggal=tanggal,
                waktu=waktu,
                tipe='cash',
                jumlah=amount,
                sumber='manual',
                keterangan='',
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id,
                message_id=update.message.message_id
            )

            await update.message.reply_text(f"✅ Cash akhir {format_rupiah(amount)} tersimpan")
            logger.info(f"Cash saved: {amount}")

        except Exception as e:
            logger.error(f"Error in cash_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def tf_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /tf <amount>"""
        try:
            if not context.args:
                await update.message.reply_text("❌ Format: /tf <jumlah>\nContoh: /tf 800k")
                return

            amount_str = ' '.join(context.args)

            try:
                amount = parse_amount(amount_str)
            except ValueError as e:
                await update.message.reply_text(f"❌ Format tidak valid: {str(e)}\n\n✅ Data TIDAK tersimpan.")
                return

            if amount <= 0:
                await update.message.reply_text("❌ Jumlah harus > 0\n\n✅ Data TIDAK tersimpan.")
                return

            tanggal = datetime.now().strftime('%Y-%m-%d')
            waktu = datetime.now().strftime('%H:%M:%S')

            self.storage.add_transaction(
                tanggal=tanggal,
                waktu=waktu,
                tipe='tf',
                jumlah=amount,
                sumber='manual',
                keterangan='',
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id,
                message_id=update.message.message_id
            )

            await update.message.reply_text(f"✅ Transfer/QRIS {format_rupiah(amount)} tercatat")
            logger.info(f"TF saved: {amount}")

        except Exception as e:
            logger.error(f"Error in tf_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def keluar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /keluar <amount> [keterangan]"""
        try:
            if not context.args:
                await update.message.reply_text("❌ Format: /keluar <jumlah> [ket]\nContoh: /keluar 200k beli gas")
                return

            full_text = ' '.join(context.args)
            tokens = full_text.split()
            amount_tokens = []
            keterangan_tokens = []
            found_text = False

            for token in tokens:
                if not found_text:
                    if token == '+':
                        amount_tokens.append('+')
                    elif self._is_amount_token(token):
                        amount_tokens.append(token)
                    else:
                        found_text = True
                        keterangan_tokens.append(token)
                else:
                    keterangan_tokens.append(token)

            amount_str = ' '.join(amount_tokens) if amount_tokens else ''
            keterangan = ' '.join(keterangan_tokens) if keterangan_tokens else ''

            if not amount_str:
                await update.message.reply_text("❌ Format: /keluar <jumlah> [ket]\nContoh: /keluar 2k + 4k operasional")
                return

            try:
                amount = parse_amount(amount_str)
            except ValueError as e:
                await update.message.reply_text(f"❌ Format tidak valid: {str(e)}\n\n✅ Data TIDAK tersimpan.")
                return

            if amount <= 0:
                await update.message.reply_text("❌ Jumlah harus > 0\n\n✅ Data TIDAK tersimpan.")
                return

            tanggal = datetime.now().strftime('%Y-%m-%d')
            waktu = datetime.now().strftime('%H:%M:%S')

            self.storage.add_transaction(
                tanggal=tanggal,
                waktu=waktu,
                tipe='keluar',
                jumlah=amount,
                sumber='manual',
                keterangan=keterangan,
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id,
                message_id=update.message.message_id
            )

            msg = f"✅ Pengeluaran {format_rupiah(amount)} tercatat"
            if keterangan:
                msg += f"\n📝 {keterangan}"

            await update.message.reply_text(msg)
            logger.info(f"Pengeluaran saved: {amount}")

        except Exception as e:
            logger.error(f"Error in keluar_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    def _is_amount_token(self, token: str) -> bool:
        """Helper untuk cek apakah token adalah angka"""
        pattern = r'^[\d\.,]+[kmjtrbibulanosnd]*$'
        return bool(re.match(pattern, token.lower()))

    async def totalpos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /totalpos <amount>"""
        try:
            if not context.args:
                await update.message.reply_text("❌ Format: /totalpos <jumlah>\nContoh: /totalpos 2.1jt")
                return

            amount_str = ' '.join(context.args)

            try:
                amount = parse_amount(amount_str)
            except ValueError as e:
                await update.message.reply_text(f"❌ Format tidak valid: {str(e)}\n\n✅ Data TIDAK tersimpan.")
                return

            if amount < 0:
                await update.message.reply_text("❌ Jumlah tidak boleh negatif\n\n✅ Data TIDAK tersimpan.")
                return

            tanggal = datetime.now().strftime('%Y-%m-%d')
            waktu = datetime.now().strftime('%H:%M:%S')

            self.storage.add_transaction(
                tanggal=tanggal,
                waktu=waktu,
                tipe='pos',
                jumlah=amount,
                sumber='manual',
                keterangan='',
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id,
                message_id=update.message.message_id
            )

            await update.message.reply_text(f"✅ Total POS {format_rupiah(amount)} tersimpan")
            logger.info(f"POS saved: {amount}")

        except Exception as e:
            logger.error(f"Error in totalpos_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /status - rekap keuangan hari ini"""
        try:
            tanggal = datetime.now().strftime('%Y-%m-%d')
            tanggal_display = datetime.now().strftime('%A, %d %B %Y')

            try:
                import locale
                locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
                tanggal_display = datetime.now().strftime('%A, %d %B %Y')
            except:
                pass

            summary = self.logic.calculate_daily_summary(tanggal)

            # Format output yang lebih rapi dan eye-catching
            message = f"""
╔══════════════════════════╗
║  📊 STATUS HARI INI  ║
╚══════════════════════════╝
📅 {tanggal_display}

━━━━━━━━━━━━━━━━━━━━━━━━
💰 MODAL & CASH
━━━━━━━━━━━━━━━━━━━━━━━━
Modal Awal       : {format_rupiah(summary['modal'])}
Cash Akhir (laci): {format_rupiah(summary['cash_akhir'])}

━━━━━━━━━━━━━━━━━━━━━━━━
💳 TRANSAKSI
━━━━━━━━━━━━━━━━━━━━━━━━
Total TF/QRIS    : {format_rupiah(summary['total_tf'])} ({summary['count_tf']}x)
Total Pengeluaran: {format_rupiah(summary['total_pengeluaran'])} ({summary['count_pengeluaran']}x)

━━━━━━━━━━━━━━━━━━━━━━━━
📈 PERHITUNGAN
━━━━━━━━━━━━━━━━━━━━━━━━
Penjualan Cash   : {format_rupiah(summary['penjualan_cash'])}
Omzet Manual     : {format_rupiah(summary['omzet_manual'])}

━━━━━━━━━━━━━━━━━━━━━━━━
🖥️ OMZET POS
━━━━━━━━━━━━━━━━━━━━━━━━
Omzet POS        : {format_rupiah(summary['pos_total'])} ({summary['count_pos']}x)

━━━━━━━━━━━━━━━━━━━━━━━━
📊 SELISIH
━━━━━━━━━━━━━━━━━━━━━━━━
Manual - POS     : {format_rupiah(summary['selisih'])} ({summary['selisih_persen']:.2f}%)

{summary['status_icon']} {summary['status_text']}
"""

            await update.message.reply_text(message)
            logger.info(f"Status requested")

        except Exception as e:
            logger.error(f"Error in status_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def lihat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /lihat - list transaksi hari ini"""
        try:
            tanggal = datetime.now().strftime('%Y-%m-%d')
            tanggal_display = datetime.now().strftime('%A, %d %B %Y')

            try:
                import locale
                locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
                tanggal_display = datetime.now().strftime('%A, %d %B %Y')
            except:
                pass

            transactions = self.storage.get_transactions_by_date(tanggal)
            summary = self.logic.calculate_daily_summary(tanggal)

            message = f"""
╔══════════════════════════╗
║  📒 TRANSAKSI HARI INI  ║
╚══════════════════════════╝
📅 {tanggal_display}

"""

            if not transactions:
                message += "📭 _Belum ada transaksi hari ini_\n"
            else:
                tipe_emoji = {
                    'modal': '💰',
                    'cash': '💵',
                    'tf': '💳',
                    'keluar': '📤',
                    'pos': '🖥️'
                }

                tipe_label = {
                    'modal': 'MODAL',
                    'cash': 'CASH',
                    'tf': 'TF',
                    'keluar': 'KELUAR',
                    'pos': 'POS'
                }

                for i, tx in enumerate(transactions, 1):
                    tx_id = tx[0]
                    waktu = tx[2][:5]  # HH:MM saja
                    tipe = tx[3]
                    jumlah = tx[4]
                    keterangan = tx[6] if tx[6] else ''

                    emoji = tipe_emoji.get(tipe, '📝')
                    label = tipe_label.get(tipe, tipe.upper())

                    line = f"{i}. [{waktu}] {emoji} {label}: {format_rupiah(jumlah)}"
                    if keterangan:
                        line += f"\n   💬 {keterangan}"
                    line += f"\n   🔑 ID: {tx_id}\n"

                    message += line

            # Summary
            message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━
📊 RINGKASAN
━━━━━━━━━━━━━━━━━━━━━━━━
💰 Modal         : {format_rupiah(summary['modal'])}
💵 Cash Akhir    : {format_rupiah(summary['cash_akhir'])}
💳 TF/QRIS       : {format_rupiah(summary['total_tf'])} ({summary['count_tf']}x)
📤 Pengeluaran   : {format_rupiah(summary['total_pengeluaran'])} ({summary['count_pengeluaran']}x)
📈 Omzet Manual  : {format_rupiah(summary['omzet_manual'])}
🖥️ Omzet POS     : {format_rupiah(summary['pos_total'])}
📊 Selisih       : {format_rupiah(summary['selisih'])} ({summary['selisih_persen']:.2f}%)

💡 Gunakan /edit <ID> untuk edit transaksi
"""

            await update.message.reply_text(message)
            logger.info(f"Lihat requested")

        except Exception as e:
            logger.error(f"Error in lihat_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def edit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /edit [ID]"""
        try:
            # Jika tidak ada argumen, tampilkan transaksi hari ini untuk dipilih
            if not context.args:
                tanggal = datetime.now().strftime('%Y-%m-%d')
                transactions = self.storage.get_recent_transactions(tanggal, limit=20)

                if not transactions:
                    await update.message.reply_text("📭 Belum ada transaksi hari ini")
                    return

                message = "🔧 *EDIT TRANSAKSI*\n\n"
                message += "Pilih transaksi yang ingin diedit:\n\n"

                tipe_emoji = {'modal': '💰', 'cash': '💵', 'tf': '💳', 'keluar': '📤', 'pos': '🖥️'}

                for tx in transactions[:10]:  # Tampilkan 10 terbaru
                    tx_id = tx[0]
                    waktu = tx[2][:5]
                    tipe = tx[3]
                    jumlah = tx[4]
                    ket = tx[6] if tx[6] else ''

                    emoji = tipe_emoji.get(tipe, '📝')
                    line = f"🔑 ID: `{tx_id}` - [{waktu}] {emoji} {format_rupiah(jumlah)}"
                    if ket:
                        line += f"\n   💬 {ket}"
                    message += line + "\n\n"

                message += "\n📝 Cara edit:\n"
                message += "1️⃣ Hapus: `/edit <ID> hapus`\n"
                message += "2️⃣ Ubah jumlah: `/edit <ID> <jumlah_baru>`\n"
                message += "3️⃣ Ubah ket: `/edit <ID> ket <keterangan_baru>`\n\n"
                message += "Contoh:\n"
                message += "• `/edit 123 hapus`\n"
                message += "• `/edit 123 150k`\n"
                message += "• `/edit 123 ket beli gas`"

                await update.message.reply_text(message, parse_mode='Markdown')
                return

            # Parse argumen
            tx_id = int(context.args[0])

            # Cek transaksi ada
            tx = self.storage.get_transaction_by_id(tx_id)
            if not tx:
                await update.message.reply_text(f"❌ Transaksi ID {tx_id} tidak ditemukan")
                return

            # Jika hanya ID, tampilkan detail
            if len(context.args) == 1:
                tipe_emoji = {'modal': '💰', 'cash': '💵', 'tf': '💳', 'keluar': '📤', 'pos': '🖥️'}
                emoji = tipe_emoji.get(tx[3], '📝')

                message = f"📝 *DETAIL TRANSAKSI*\n\n"
                message += f"🔑 ID: `{tx[0]}`\n"
                message += f"📅 Tanggal: {tx[1]}\n"
                message += f"🕐 Waktu: {tx[2]}\n"
                message += f"{emoji} Tipe: {tx[3].upper()}\n"
                message += f"💵 Jumlah: {format_rupiah(tx[4])}\n"
                if tx[6]:
                    message += f"💬 Keterangan: {tx[6]}\n"

                message += "\n📝 Cara edit:\n"
                message += f"• Hapus: `/edit {tx_id} hapus`\n"
                message += f"• Ubah jumlah: `/edit {tx_id} <jumlah>`\n"
                message += f"• Ubah ket: `/edit {tx_id} ket <text>`"

                await update.message.reply_text(message, parse_mode='Markdown')
                return

            # Action: hapus
            if context.args[1].lower() == 'hapus':
                self.storage.delete_transaction(tx_id)
                await update.message.reply_text(f"✅ Transaksi ID {tx_id} berhasil dihapus")
                logger.info(f"Transaction deleted: ID={tx_id}")
                return

            # Action: ubah keterangan
            if context.args[1].lower() == 'ket' or context.args[1].lower() == 'keterangan':
                if len(context.args) < 3:
                    await update.message.reply_text("❌ Format: /edit <ID> ket <keterangan_baru>")
                    return
                new_ket = ' '.join(context.args[2:])
                self.storage.update_transaction(tx_id, keterangan=new_ket)
                await update.message.reply_text(f"✅ Keterangan transaksi ID {tx_id} diubah menjadi:\n💬 {new_ket}")
                logger.info(f"Transaction updated: ID={tx_id}, new_ket={new_ket}")
                return

            # Action: ubah jumlah
            amount_str = ' '.join(context.args[1:])
            try:
                new_amount = parse_amount(amount_str)
            except ValueError as e:
                await update.message.reply_text(f"❌ Format tidak valid: {str(e)}")
                return

            if new_amount < 0:
                await update.message.reply_text("❌ Jumlah tidak boleh negatif")
                return

            self.storage.update_transaction(tx_id, jumlah=new_amount)
            await update.message.reply_text(f"✅ Jumlah transaksi ID {tx_id} diubah menjadi:\n💵 {format_rupiah(new_amount)}")
            logger.info(f"Transaction updated: ID={tx_id}, new_amount={new_amount}")

        except ValueError:
            await update.message.reply_text("❌ ID harus berupa angka\nContoh: /edit 123")
        except Exception as e:
            logger.error(f"Error in edit_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def photo_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk foto (OCR via Gemini)"""
        try:
            # 1. Download foto kualitas tertinggi
            if not update.message.photo:
                return

            photo = update.message.photo[-1]
            file_id = photo.file_id

            # Beri feedback sedang memproses
            processing_msg = await update.message.reply_text("⏳ Sedang menganalisa gambar...")

            # Download file
            new_file = await context.bot.get_file(file_id)
            file_byte_array = await new_file.download_as_bytearray()
            file_bytes = bytes(file_byte_array)

            # 2. Kirim ke Gemini
            if not self.gemini or not self.gemini.model:
                await processing_msg.edit_text("⚠️ Fitur OCR belum dikonfigurasi (API Key missing).")
                return

            result = self.gemini.analyze_transfer_image(file_bytes)

            # 3. Proses hasil
            if result['is_transfer'] and result['amount'] > 0:
                amount = result['amount']
                confidence = result['confidence']
                reason = result.get('reason', 'Transfer detected')

                tanggal = datetime.now().strftime('%Y-%m-%d')
                waktu = datetime.now().strftime('%H:%M:%S')

                # Simpan transaksi
                tx_id = self.storage.add_transaction(
                    tanggal=tanggal,
                    waktu=waktu,
                    tipe='tf',
                    jumlah=amount,
                    sumber='ocr_gemini',
                    keterangan=f"OCR: {reason}",
                    chat_id=update.effective_chat.id,
                    user_id=update.effective_user.id,
                    message_id=update.message.message_id,
                    file_id=file_id
                )

                # Feedback sukses
                await processing_msg.edit_text(
                    f"✅ *TRANSFER TERDETEKSI*\n\n"
                    f"💰 Nominal: {format_rupiah(amount)}\n"
                    f"📝 Catatan: {reason}\n"
                    f"🤖 Confidence: {int(confidence * 100)}%\n\n"
                    f"Data berhasil disimpan sebagai transaksi TF hari ini.",
                    parse_mode='Markdown'
                )
                logger.info(f"OCR Success: {amount} from user {update.effective_user.id}")

            else:
                # Feedback gagal
                reason = result.get('reason', 'Tidak terdeteksi sebagai bukti transfer')
                await processing_msg.edit_text(
                    f"⚠️ *OCR TIDAK YAKIN*\n\n"
                    f"Analisa AI: {reason}\n\n"
                    f"Silakan input manual dengan:\n"
                    f"`/tf <jumlah>`",
                    parse_mode='Markdown'
                )
                logger.info(f"OCR Failed/Ignored: {reason}")

        except Exception as e:
            logger.error(f"Error in photo_handler: {e}")
            await update.message.reply_text("❌ Gagal memproses gambar")

    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /reset - reset transaksi hari ini"""
        try:
            tanggal = datetime.now().strftime('%Y-%m-%d')

            # Cek apakah ada transaksi hari ini
            transactions = self.storage.get_transactions_by_date(tanggal)

            if not transactions:
                await update.message.reply_text("📭 Belum ada transaksi hari ini untuk direset")
                return

            # Tampilkan konfirmasi
            count = len(transactions)
            keyboard = [
                [
                    InlineKeyboardButton("✅ Ya, Reset", callback_data=f"confirm_reset_{tanggal}"),
                    InlineKeyboardButton("❌ Batal", callback_data="cancel_reset")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"⚠️ *KONFIRMASI RESET*\n\n"
                f"Anda akan menghapus *SEMUA {count} transaksi* hari ini:\n"
                f"📅 {tanggal}\n\n"
                f"⚠️ Tindakan ini tidak dapat dibatalkan!\n\n"
                f"Lanjutkan?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in reset_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk inline button callback"""
        query = update.callback_query
        await query.answer()

        data = query.data

        # Handle reset dan modal baru
        if data.startswith('reset_and_modal_'):
            try:
                amount = int(data.split('_')[3])
                tanggal = datetime.now().strftime('%Y-%m-%d')
                waktu = datetime.now().strftime('%H:%M:%S')

                # Hapus semua transaksi hari ini
                deleted_count = self.storage.delete_all_transactions_by_date(tanggal)

                # Simpan modal baru
                self.storage.add_transaction(
                    tanggal=tanggal,
                    waktu=waktu,
                    tipe='modal',
                    jumlah=amount,
                    sumber='manual',
                    keterangan='',
                    chat_id=update.effective_chat.id,
                    user_id=query.from_user.id,
                    message_id=query.message.message_id
                )

                await query.edit_message_text(
                    f"✅ Reset berhasil!\n\n"
                    f"🗑️ {deleted_count} transaksi lama dihapus\n"
                    f"💰 Modal awal {format_rupiah(amount)} tersimpan\n"
                    f"📅 Transaksi hari ini dimulai dari awal"
                )
                logger.info(f"Reset and new modal: {amount}, deleted: {deleted_count}")

            except Exception as e:
                logger.error(f"Error in reset_and_modal: {e}")
                await query.edit_message_text("❌ Terjadi kesalahan")

        elif data == 'cancel_modal':
            await query.edit_message_text("❌ Input modal dibatalkan")

        # Handle konfirmasi reset
        elif data.startswith('confirm_reset_'):
            try:
                tanggal = data.split('_')[2]
                deleted_count = self.storage.delete_all_transactions_by_date(tanggal)

                await query.edit_message_text(
                    f"✅ Reset berhasil!\n\n"
                    f"🗑️ {deleted_count} transaksi telah dihapus\n"
                    f"📅 {tanggal}\n\n"
                    f"💡 Gunakan /modal untuk memulai transaksi baru"
                )
                logger.info(f"Manual reset: {tanggal}, deleted: {deleted_count}")

            except Exception as e:
                logger.error(f"Error in confirm_reset: {e}")
                await query.edit_message_text("❌ Terjadi kesalahan")

        elif data == 'cancel_reset':
            await query.edit_message_text("❌ Reset dibatalkan")

        # Handle OCR save
        elif data.startswith('ocr_save_'):
            parts = data.split('_')
            if len(parts) >= 4:
                amount = int(parts[2])
                original_msg_id = int(parts[3])

                tanggal = datetime.now().strftime('%Y-%m-%d')
                waktu = datetime.now().strftime('%H:%M:%S')

                self.storage.add_transaction(
                    tanggal=tanggal,
                    waktu=waktu,
                    tipe='tf',
                    jumlah=amount,
                    sumber='ocr',
                    keterangan='Via OCR',
                    chat_id=update.effective_chat.id,
                    user_id=query.from_user.id,
                    message_id=original_msg_id
                )

                await query.edit_message_text(f"✅ Transfer {format_rupiah(amount)} dari OCR tersimpan")
                logger.info(f"OCR transaction saved: {amount}")

        elif data.startswith('ocr_cancel_'):
            await query.edit_message_text("❌ Transaksi OCR dibatalkan")
            logger.info("OCR cancelled")

    def run(self):
        """Jalankan bot"""
        application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()

        # Register handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("modal", self.modal_command))
        application.add_handler(CommandHandler("cash", self.cash_command))
        application.add_handler(CommandHandler("tf", self.tf_command))
        application.add_handler(CommandHandler("keluar", self.keluar_command))
        application.add_handler(CommandHandler("totalpos", self.totalpos_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("lihat", self.lihat_command))
        application.add_handler(CommandHandler("edit", self.edit_command))
        application.add_handler(CommandHandler("reset", self.reset_command))

        application.add_handler(MessageHandler(filters.PHOTO, self.photo_handler))
        application.add_handler(CallbackQueryHandler(self.callback_query_handler))

        logger.info("Bot started...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    bot = TokoBot()
    bot.run()
