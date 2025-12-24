"""
Asisten Keuangan Anisa Store v2
Bot Telegram untuk Pencatatan Keuangan Harian Toko
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
from scheduler import RekapScheduler
from datetime import datetime, timedelta

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
        self.scheduler = RekapScheduler(self.storage, self.logic)

    def _get_username(self, user) -> str:
        """Get username from Telegram user object for audit logging."""
        if user.username:
            return f"@{user.username}"
        elif user.first_name:
            return user.first_name
        else:
            return f"user_{user.id}"

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk command /start"""
        keyboard = [
            [InlineKeyboardButton("➕ Input Transaksi", callback_data="menu_input")],
            [InlineKeyboardButton("📊 Rekap & Laporan", callback_data="menu_rekap")],
            [InlineKeyboardButton("✏️ Koreksi & Reset", callback_data="menu_koreksi")],
            [InlineKeyboardButton("❓ Bantuan", callback_data="menu_bantuan")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🏪 *Asisten Keuangan Anisa Store v2*\n\n"
            "Selamat datang! Pilih menu di bawah atau ketik /help untuk bantuan.\n\n"
            "💡 _Tip: Kirim foto bukti transfer untuk OCR otomatis_",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

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
                username=self._get_username(update.effective_user),
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
                username=self._get_username(update.effective_user),
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
                username=self._get_username(update.effective_user),
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
                username=self._get_username(update.effective_user),
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
                username=self._get_username(update.effective_user),
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

            # Action buttons untuk quick actions
            keyboard = [
                [
                    InlineKeyboardButton("➕ Tambah", callback_data="menu_input"),
                    InlineKeyboardButton("✏️ Koreksi", callback_data="action_edit")
                ],
                [
                    InlineKeyboardButton("📊 Rekap", callback_data="menu_rekap"),
                    InlineKeyboardButton("🧹 Reset", callback_data="action_reset_today")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(message, reply_markup=reply_markup)
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
                username = self._get_username(update.effective_user)
                self.storage.delete_transaction(tx_id, username=username)
                await update.message.reply_text(f"✅ Transaksi ID {tx_id} berhasil dihapus")
                logger.info(f"Transaction deleted: ID={tx_id} by {username}")
                return

            # Action: ubah keterangan
            if context.args[1].lower() == 'ket' or context.args[1].lower() == 'keterangan':
                if len(context.args) < 3:
                    await update.message.reply_text("❌ Format: /edit <ID> ket <keterangan_baru>")
                    return
                new_ket = ' '.join(context.args[2:])
                username = self._get_username(update.effective_user)
                self.storage.update_transaction(tx_id, username=username, keterangan=new_ket)
                await update.message.reply_text(f"✅ Keterangan transaksi ID {tx_id} diubah menjadi:\n💬 {new_ket}")
                logger.info(f"Transaction updated: ID={tx_id}, new_ket={new_ket} by {username}")
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

            username = self._get_username(update.effective_user)
            self.storage.update_transaction(tx_id, username=username, jumlah=new_amount)
            await update.message.reply_text(f"✅ Jumlah transaksi ID {tx_id} diubah menjadi:\n💵 {format_rupiah(new_amount)}")
            logger.info(f"Transaction updated: ID={tx_id}, new_amount={new_amount} by {username}")

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
                    username=self._get_username(update.effective_user),
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
        """Handler untuk /reset [YYYY-MM-DD] - reset transaksi hari ini atau tanggal tertentu"""
        try:
            import re

            # Check if date argument provided
            if context.args:
                date_str = context.args[0]
                # Validate date format
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                    await update.message.reply_text(
                        "❌ Format tanggal salah.\n\n"
                        "Gunakan format: `/reset YYYY-MM-DD`\n"
                        "Contoh: `/reset 2025-12-11`",
                        parse_mode='Markdown'
                    )
                    return
                tanggal = date_str
                is_today = (tanggal == datetime.now().strftime('%Y-%m-%d'))
            else:
                tanggal = datetime.now().strftime('%Y-%m-%d')
                is_today = True

            # Cek apakah ada transaksi untuk tanggal ini
            transactions = self.storage.get_transactions_by_date(tanggal)

            if not transactions:
                if is_today:
                    await update.message.reply_text("📭 Belum ada transaksi hari ini untuk direset")
                else:
                    await update.message.reply_text(f"📭 Tidak ada transaksi tanggal {tanggal}")
                return

            # Tampilkan konfirmasi (2-step)
            count = len(transactions)
            keyboard = [
                [
                    InlineKeyboardButton("✅ Ya, Reset", callback_data=f"confirm_reset_{tanggal}"),
                    InlineKeyboardButton("❌ Batal", callback_data="cancel_reset")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            date_label = "hari ini" if is_today else f"tanggal {tanggal}"
            await update.message.reply_text(
                f"⚠️ *KONFIRMASI RESET*\n\n"
                f"Anda akan menghapus *{count} transaksi* {date_label}.\n\n"
                f"📅 {tanggal}\n\n"
                f"⚠️ Tindakan ini tidak dapat dibatalkan!\n"
                f"💡 Rekap yang sudah tersimpan akan direvisi, bukan dihapus.\n\n"
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
                    username=self._get_username(query.from_user),
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

                # Check if there's an existing summary for this date
                existing_summary = self.storage.get_latest_summary_by_date(tanggal)

                # Delete all transactions
                deleted_count = self.storage.delete_all_transactions_by_date(tanggal)

                # If there was an existing summary, create a REVISED version
                # This preserves the history that there was a reset
                if existing_summary:
                    # Calculate new summary (should be zeros or whatever is left)
                    new_summary_data = self.logic.calculate_daily_summary(tanggal)
                    self.storage.save_daily_summary(
                        date=tanggal,
                        state='REVISED',
                        summary_data=new_summary_data,
                        notes=f'Reset: {deleted_count} transaksi dihapus'
                    )
                    logger.info(f"Created REVISED summary for {tanggal} after reset")

                await query.edit_message_text(
                    f"✅ Reset berhasil!\n\n"
                    f"🗑️ {deleted_count} transaksi telah dihapus\n"
                    f"📅 {tanggal}\n"
                    f"🔄 Rekap direvisi (tidak dihapus)\n\n"
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
                    username=self._get_username(query.from_user),
                    message_id=original_msg_id
                )

                await query.edit_message_text(f"✅ Transfer {format_rupiah(amount)} dari OCR tersimpan")
                logger.info(f"OCR transaction saved: {amount}")

        elif data.startswith('ocr_cancel_'):
            await query.edit_message_text("❌ Transaksi OCR dibatalkan")
            logger.info("OCR cancelled")

        # ===== MENU HANDLERS (v2) =====
        elif data == 'menu_input':
            keyboard = [
                [
                    InlineKeyboardButton("💵 Cash", callback_data="input_cash"),
                    InlineKeyboardButton("💳 Transfer", callback_data="input_tf")
                ],
                [
                    InlineKeyboardButton("📤 Pengeluaran", callback_data="input_keluar"),
                    InlineKeyboardButton("💰 Modal", callback_data="input_modal")
                ],
                [
                    InlineKeyboardButton("🖥️ Total POS", callback_data="input_pos"),
                    InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_main")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "➕ *Input Transaksi*\n\nPilih jenis transaksi:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif data == 'menu_rekap':
            keyboard = [
                [InlineKeyboardButton("📊 Status Hari Ini", callback_data="rekap_today")],
                [InlineKeyboardButton("✅ Finalisasi Rekap Hari Ini", callback_data="action_fix_daily")],
                [InlineKeyboardButton("📅 Rekap Mingguan", callback_data="rekap_weekly")],
                [InlineKeyboardButton("📆 Rekap Bulanan", callback_data="rekap_monthly")],
                [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📊 *Rekap & Laporan*\n\nPilih jenis laporan:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif data == 'menu_koreksi':
            keyboard = [
                [InlineKeyboardButton("✏️ Edit Transaksi Hari Ini", callback_data="action_edit")],
                [InlineKeyboardButton("📅 Edit Rekap Tanggal Lalu", callback_data="action_editrekap")],
                [InlineKeyboardButton("📜 Riwayat Perubahan", callback_data="action_riwayat")],
                [InlineKeyboardButton("🧹 Reset Hari Ini", callback_data="action_reset_today")],
                [InlineKeyboardButton("📅 Reset Tanggal Lain", callback_data="action_reset_date")],
                [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "✏️ *Koreksi & Reset*\n\n"
                "Pilih aksi yang ingin dilakukan:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif data == 'menu_bantuan':
            help_text = """
❓ *Bantuan Singkat*

• `/modal 500k` - Modal awal
• `/cash 1jt` - Cash akhir
• `/tf 200k` - Transfer masuk
• `/keluar 50k beli bensin` - Pengeluaran

_Ketik /help untuk panduan lengkap._
"""
            keyboard = [[InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

        elif data == 'menu_main':
            # Call menu_command logic directly
            await self.menu_command(update, context)

        elif data == 'menu_close':
            await query.edit_message_text("✅ Menu ditutup")

        # ===== INPUT VIA BUTTON (STATE MACHINE) =====
        elif data.startswith('input_'):
            input_type = data.replace('input_', '')
            type_names = {
                'cash': ('Cash Akhir', '/cash'),
                'tf': ('Transfer/QRIS', '/tf'),
                'keluar': ('Pengeluaran', '/keluar'),
                'modal': ('Modal Awal', '/modal'),
                'pos': ('Total POS', '/totalpos')
            }
            name, cmd = type_names.get(input_type, ('Transaksi', ''))

            # Set state for text handler
            context.user_data['pending_input'] = input_type

            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu_input")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"💰 *Input {name}*\n\n"
                f"Ketik nominal:\n"
                f"_Contoh: 850k atau 2jt + 500rb_\n\n"
                f"Atau gunakan command: `{cmd} <jumlah>`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        # ===== ACTION HANDLERS =====
        elif data == 'action_fix_daily':
             tanggal = datetime.now().strftime('%Y-%m-%d')

             # Calculate and save as FINAL
             summary = self.logic.calculate_daily_summary(tanggal)
             self.storage.save_daily_summary(
                 date=tanggal,
                 state='FINAL',
                 summary_data=summary,
                 notes='Manual Finalization via Menu'
             )

             await query.answer("✅ Rekap harian difinalisasi!")
             await query.edit_message_text(
                 f"✅ *Rekap Harian Final*\n"
                 f"📅 {tanggal}\n\n"
                 f"Data telah disimpan sebagai FINAL dan akan masuk perhitungan mingguan/bulanan.",
                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="menu_rekap")]])
             )

        elif data == 'action_edit':
            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu_koreksi")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "✏️ *Edit Transaksi*\n\n"
                "Gunakan command:\n"
                "• `/edit` - lihat daftar transaksi\n"
                "• `/edit <ID> hapus` - hapus\n"
                "• `/edit <ID> <nominal>` - ubah nominal",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif data == 'action_reset_today':
            tanggal = datetime.now().strftime('%Y-%m-%d')
            transactions = self.storage.get_transactions_by_date(tanggal)

            if not transactions:
                await query.edit_message_text(
                    "📭 Belum ada transaksi hari ini",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="menu_koreksi")]])
                )
                return

            count = len(transactions)
            keyboard = [
                [
                    InlineKeyboardButton("✅ Ya, Reset", callback_data=f"confirm_reset_{tanggal}"),
                    InlineKeyboardButton("❌ Batal", callback_data="menu_koreksi")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"⚠️ *KONFIRMASI RESET*\n\n"
                f"Hapus *{count} transaksi* hari ini ({tanggal})?\n\n"
                f"⚠️ Tindakan ini tidak dapat dibatalkan!",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif data == 'action_reset_date':
            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu_koreksi")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📅 *Reset Tanggal Lain*\n\n"
                "Gunakan command:\n"
                "`/reset YYYY-MM-DD`\n\n"
                "Contoh: `/reset 2025-12-11`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif data == 'action_editrekap':
            # Menu utama edit rekap dengan pilihan mingguan/bulanan
            keyboard = [
                [InlineKeyboardButton("📅 Lihat 1 Minggu Terakhir", callback_data="editrekap_week")],
                [InlineKeyboardButton("📆 Lihat 1 Bulan Terakhir", callback_data="editrekap_month")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_koreksi")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📅 *Edit Rekap Tanggal Lalu*\n\n"
                "Pilih periode untuk melihat selisih per hari:\n"
                "_Atau gunakan `/editrekap YYYY-MM-DD`_",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif data == 'editrekap_week':
            # Tampilkan 7 hari terakhir dengan selisih
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)

            summaries = self.storage.get_summaries_range(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            # Create dict for easy lookup
            summary_dict = {s[1]: s for s in summaries}

            message = "📅 *SELISIH MINGGU INI*\n"
            message += f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')}\n\n"

            keyboard = []
            total_selisih = 0

            for i in range(7):
                d = end_date - timedelta(days=6-i)
                date_str = d.strftime('%Y-%m-%d')
                label = d.strftime('%d %b')

                if date_str in summary_dict:
                    s = summary_dict[date_str]
                    selisih = s[14]
                    total_selisih += selisih
                    status = s[17]

                    if selisih > 5000:
                        icon = "🔴"
                    elif selisih < -5000:
                        icon = "🔴"
                    elif abs(selisih) > 1000:
                        icon = "🟡"
                    else:
                        icon = "🟢"

                    selisih_str = f"+{format_rupiah(selisih)}" if selisih >= 0 else format_rupiah(selisih)
                    message += f"{icon} {label}: {selisih_str} {status}\n"
                    keyboard.append([InlineKeyboardButton(f"{icon} {label}: {selisih_str}", callback_data=f"editrekap_{date_str}")])
                else:
                    message += f"⚪ {label}: _belum ada data_\n"
                    keyboard.append([InlineKeyboardButton(f"⚪ {label}: No data", callback_data=f"editrekap_{date_str}")])

            total_str = f"+{format_rupiah(total_selisih)}" if total_selisih >= 0 else format_rupiah(total_selisih)
            message += f"\n━━━━━━━━━━━━━━\n📊 *Total Selisih: {total_str}*"

            keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="action_editrekap")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        elif data == 'editrekap_month':
            # Tampilkan 30 hari terakhir dengan selisih
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=29)

            summaries = self.storage.get_summaries_range(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            summary_dict = {s[1]: s for s in summaries}

            message = "📆 *SELISIH BULAN INI*\n"
            message += f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')}\n\n"

            # Group by status
            big_plus = []  # > 5k
            big_minus = []  # < -5k
            small = []  # -5k to 5k
            total_selisih = 0

            for i in range(30):
                d = end_date - timedelta(days=29-i)
                date_str = d.strftime('%Y-%m-%d')

                if date_str in summary_dict:
                    s = summary_dict[date_str]
                    selisih = s[14]
                    total_selisih += selisih
                    status = s[17]

                    if selisih > 5000:
                        big_plus.append((date_str, selisih, status))
                    elif selisih < -5000:
                        big_minus.append((date_str, selisih, status))
                    else:
                        small.append((date_str, selisih, status))

            # Show problematic days first
            keyboard = []

            if big_plus or big_minus:
                message += "🚨 *Selisih Besar (perlu dicek):*\n"
                for date_str, selisih, status in (big_plus + big_minus)[:10]:
                    d = datetime.strptime(date_str, '%Y-%m-%d')
                    label = d.strftime('%d %b')
                    selisih_str = f"+{format_rupiah(selisih)}" if selisih >= 0 else format_rupiah(selisih)
                    message += f"🔴 {label}: {selisih_str} {status}\n"
                    keyboard.append([InlineKeyboardButton(f"🔴 {label}: {selisih_str}", callback_data=f"editrekap_{date_str}")])

            if small:
                message += f"\n✅ Hari dengan selisih kecil: {len(small)} hari\n"

            message += f"\n━━━━━━━━━━━━━━\n"
            total_str = f"+{format_rupiah(total_selisih)}" if total_selisih >= 0 else format_rupiah(total_selisih)
            message += f"📊 *Total Selisih (30 hari): {total_str}*\n"
            message += f"📅 Data tersedia: {len(summaries)} hari"

            keyboard.append([InlineKeyboardButton("📅 Lihat Semua (Mingguan)", callback_data="editrekap_week")])
            keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="action_editrekap")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        elif data.startswith('editrekap_'):
            date_str = data.replace('editrekap_', '')
            transactions = self.storage.get_transactions_by_date(date_str)

            message = f"📝 *Edit Rekap*\n📅 {date_str}\n\n"
            tipe_emoji = {'modal': '💰', 'cash': '💵', 'tf': '💳', 'keluar': '📤', 'pos': '🖥️'}

            if not transactions:
                message += "📭 _Belum ada transaksi_\n\n"
            else:
                for i, tx in enumerate(transactions[:10], 1):
                    tx_id, _, waktu, tipe, jumlah, _, ket = tx[:7]
                    emoji = tipe_emoji.get(tipe, '📝')
                    line = f"{i}. {emoji} {tipe.upper()}: {format_rupiah(jumlah)}\n   🔑 ID: `{tx_id}`\n"
                    message += line

            message += f"\n*Aksi:*\n"
            message += f"➕ `/editrekap {date_str} tambah pos 1.5jt`\n"
            message += f"🗑️ `/editrekap {date_str} hapus ID`\n"
            message += f"✏️ `/editrekap {date_str} ID JUMLAH`"

            keyboard = [
                [InlineKeyboardButton("➕ Tambah POS", callback_data=f"addtx_{date_str}_pos")],
                [
                    InlineKeyboardButton("💳 TF", callback_data=f"addtx_{date_str}_tf"),
                    InlineKeyboardButton("📤 Keluar", callback_data=f"addtx_{date_str}_keluar")
                ],
                [InlineKeyboardButton("🔙 Kembali", callback_data="action_editrekap")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        elif data.startswith('addtx_'):
            # Format: addtx_YYYY-MM-DD_tipe
            parts = data.split('_')
            if len(parts) >= 3:
                date_str = parts[1]
                tipe = parts[2]

                # Set state untuk input jumlah
                context.user_data['pending_addtx'] = {
                    'date': date_str,
                    'tipe': tipe
                }

                tipe_names = {'modal': 'Modal', 'cash': 'Cash', 'tf': 'Transfer', 'keluar': 'Pengeluaran', 'pos': 'Total POS'}
                keyboard = [[InlineKeyboardButton("❌ Batal", callback_data=f"editrekap_{date_str}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"➕ *Tambah {tipe_names.get(tipe, tipe)}*\n"
                    f"📅 Tanggal: {date_str}\n\n"
                    f"Ketik jumlah yang ingin ditambahkan:\n"
                    f"Contoh: `1.5jt`, `300k`, `500000`",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

        elif data == 'action_riwayat':
            date_str = datetime.now().strftime('%Y-%m-%d')
            logs = self.storage.get_audit_log_by_date(date_str)

            if not logs:
                message = f"📜 *Riwayat Perubahan*\n📅 {date_str}\n\nBelum ada log perubahan hari ini."
            else:
                message = f"📜 *Riwayat Perubahan*\n📅 {date_str}\n\n"
                action_emoji = {'ADD': '➕', 'EDIT': '✏️', 'DELETE': '🗑️'}

                for log in logs[:10]:
                    _, timestamp, action, _, entity_id, _, username, field, old_val, new_val, notes = log
                    try:
                        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = ts.strftime('%H:%M')
                    except:
                        time_str = '??:??'

                    emoji = action_emoji.get(action, '📝')
                    message += f"{emoji} [{time_str}] {action} oleh {username}\n"
                    if notes:
                        message += f"   💬 {notes}\n"

                if len(logs) > 10:
                    message += f"\n_...dan {len(logs) - 10} log lainnya_"
                message += f"\n\n📊 Total: {len(logs)} perubahan"

            # Tombol untuk lihat tanggal lain
            keyboard = [
                [InlineKeyboardButton("📅 Lihat Tanggal Lain", callback_data="riwayat_select_date")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_koreksi")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        elif data == 'riwayat_select_date':
            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="action_riwayat")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📜 *Riwayat Tanggal Lain*\n\n"
                "Gunakan command:\n"
                "`/riwayat YYYY-MM-DD`\n\n"
                "Contoh: `/riwayat 2025-12-20`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif data == 'rekap_weekly_detail':
            # Redirect ke command /mingguan dengan mengirim pesan baru
            end_date = datetime.now()
            start_date = end_date - timedelta(days=6)

            summaries = self.storage.get_summaries_range(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            if not summaries:
                keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="rekap_weekly")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "📭 Tidak ada data detail",
                    reply_markup=reply_markup
                )
                return

            total_omzet = sum(s[13] for s in summaries)
            total_selisih = sum(s[14] for s in summaries)
            selisih_str = f"+{format_rupiah(total_selisih)}" if total_selisih >= 0 else format_rupiah(total_selisih)

            message = f"📅 *Detail Mingguan*\n{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')}\n\n"

            for s in summaries:
                date = s[1]
                omzet = s[13]
                selisih = s[14]
                status_icon = s[17]

                selisih_sign = f"+{format_rupiah(selisih)}" if selisih >= 0 else format_rupiah(selisih)
                message += f"📅 {date}\n   💰 {format_rupiah(omzet)} | {selisih_sign} {status_icon}\n"

            message += f"\n━━━━━━━━━━━━━━━━━━━━\n📊 Total Selisih: {selisih_str}"

            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="rekap_weekly")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        # ===== REKAP HANDLERS =====
        elif data == 'rekap_today':
            await query.answer("📊 Menampilkan status...")
            # Send status as new message
            tanggal = datetime.now().strftime('%Y-%m-%d')
            summary = self.logic.calculate_daily_summary(tanggal)

            message = f"""
📊 *Status Hari Ini*
📅 {tanggal}

💰 Modal: {format_rupiah(summary['modal'])}
💵 Cash: {format_rupiah(summary['cash_akhir'])}
💳 TF: {format_rupiah(summary['total_tf'])} ({summary['count_tf']}x)
📤 Keluar: {format_rupiah(summary['total_pengeluaran'])} ({summary['count_pengeluaran']}x)
📈 Omzet: {format_rupiah(summary['omzet_manual'])}
🖥️ POS: {format_rupiah(summary['pos_total'])}
📊 Selisih: {format_rupiah(summary['selisih'])}

{summary['status_icon']} {summary['status_text']}
"""
            # Add Back button
            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu_rekap")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        elif data == 'rekap_weekly':
            await query.answer("📅 Menghitung rekap mingguan...")
            # await query.edit_message_text("⏳ Memuat rekap mingguan...")
            # (removed edit text to avoid flicker if fast)

            end_date = datetime.now()
            start_date = end_date - timedelta(days=6)

            summaries = self.storage.get_summaries_range(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu_rekap")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if not summaries:
                await query.edit_message_text(
                    "📭 *Rekap Mingguan*\n\n"
                    "Belum ada data rekap tersimpan.\n"
                    "Rekap otomatis dibuat jam 23:00 (DRAFT) dan 02:00 (FINAL).",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return

            total_omzet = sum(s[13] for s in summaries)  # omzet_manual index
            total_tf = sum(s[6] for s in summaries)  # total_tf index
            total_keluar = sum(s[8] for s in summaries)  # total_pengeluaran index
            total_pos = sum(s[10] for s in summaries)  # pos_total
            total_selisih = sum(s[14] for s in summaries)  # selisih
            days_plus = sum(1 for s in summaries if s[14] > 0)
            days_minus = sum(1 for s in summaries if s[14] < 0)

            selisih_str = f"+{format_rupiah(total_selisih)}" if total_selisih >= 0 else format_rupiah(total_selisih)
            selisih_icon = "📈" if total_selisih >= 0 else "📉"

            message = f"""
📅 *Rekap Mingguan*
{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')}

━━━━━━━━━━━━━━━━━━━━
📈 Total Omzet: {format_rupiah(total_omzet)}
🖥️ Total POS: {format_rupiah(total_pos)}
{selisih_icon} Total Selisih: {selisih_str}

📈 Hari Plus: {days_plus} | 📉 Minus: {days_minus}
📊 Tercatat: {len(summaries)} hari
━━━━━━━━━━━━━━━━━━━━

_Ketuk /mingguan untuk detail per hari_
"""
            keyboard = [
                [InlineKeyboardButton("📝 Lihat Detail", callback_data="rekap_weekly_detail")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_rekap")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        elif data == 'rekap_monthly':
            await query.answer("📆 Menghitung rekap bulanan...")
            now = datetime.now()
            start_date = now.replace(day=1)

            summaries = self.storage.get_summaries_range(
                start_date.strftime('%Y-%m-%d'),
                now.strftime('%Y-%m-%d')
            )

            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu_rekap")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if not summaries:
                await query.edit_message_text(
                    "📭 *Rekap Bulanan*\n\n"
                    "Belum ada data rekap tersimpan bulan ini.\n"
                    "Rekap otomatis dibuat jam 23:00 (DRAFT) dan 02:00 (FINAL).",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return

            total_omzet = sum(s[13] for s in summaries)
            total_tf = sum(s[6] for s in summaries)
            total_keluar = sum(s[8] for s in summaries)
            total_pos = sum(s[10] for s in summaries)
            total_selisih = sum(s[14] for s in summaries)
            days_plus = sum(1 for s in summaries if s[14] > 0)
            days_minus = sum(1 for s in summaries if s[14] < 0)

            selisih_str = f"+{format_rupiah(total_selisih)}" if total_selisih >= 0 else format_rupiah(total_selisih)
            selisih_icon = "📈" if total_selisih >= 0 else "📉"

            message = f"""
📆 *Rekap Bulanan*
{now.strftime('%B %Y')}

━━━━━━━━━━━━━━━━━━━━
📈 Total Omzet: {format_rupiah(total_omzet)}
🖥️ Total POS: {format_rupiah(total_pos)}
{selisih_icon} Total Selisih: {selisih_str}

📈 Hari Plus: {days_plus} | 📉 Minus: {days_minus}
📊 Tercatat: {len(summaries)} hari
━━━━━━━━━━━━━━━━━━━━

_Ketuk /bulanan untuk detail lengkap_
"""
            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu_rekap")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    # ===== NEW COMMAND HANDLERS (v2) =====

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk command /start"""
        # Redirect to menu_command logic
        await self.menu_command(update, context)

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /menu - menampilkan menu utama"""
        keyboard = [
            [InlineKeyboardButton("➕ Input Transaksi", callback_data="menu_input")],
            [InlineKeyboardButton("📊 Rekap & Laporan", callback_data="menu_rekap")],
            [InlineKeyboardButton("✏️ Koreksi & Reset", callback_data="menu_koreksi")],
            [InlineKeyboardButton("❓ Bantuan", callback_data="menu_bantuan")],
            [InlineKeyboardButton("❌ Tutup Menu", callback_data="menu_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Bisa dipanggil dari /start, /menu, atau callback "menu_main"
        msg_text = (
            "🏪 *Asisten Keuangan Anisa Store v2*\n\n"
            "Selamat datang! Silakan pilih menu di bawah ini.\n\n"
            "💡 _Tip: Ketik /help untuk daftar lengkap perintah_"
        )

        if update.message:
            await update.message.reply_text(msg_text, reply_markup=reply_markup, parse_mode='Markdown')
        elif update.callback_query:
            # Jika dari callback "menu_main"
            await update.callback_query.edit_message_text(msg_text, reply_markup=reply_markup, parse_mode='Markdown')


    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /help - menampilkan bantuan teks lengkap"""
        help_text = """
❓ *PANDUAN LENGKAP*

*1️⃣ Format Angka*
• Bebas: `4000`, `4k`, `4rb`, `4.000`, `4jt`
• Operasi: `2k + 500` (otomatis dihitung)

*2️⃣ Perintah Dasar*
• `/modal [jumlah]` - Input modal awal
• `/cash [jumlah]` - Input cash di laci
• `/tf [jumlah]` - Input transfer/QRIS
• `/keluar [jumlah] [ket]` - Input pengeluaran
• `/totalpos [jumlah]` - Input omzet dari program POS

*3️⃣ Laporan & Koreksi*
• `/status` - Lihat rekap hari ini
• `/mingguan` - Rekap 7 hari + total selisih
• `/bulanan` - Rekap bulan ini + total selisih
• `/lihat` - Daftar transaksi hari ini
• `/edit` - Hapus/ubah transaksi hari ini
• `/editrekap TANGGAL` - Edit rekap tanggal lalu
• `/riwayat [TANGGAL]` - Lihat riwayat perubahan
• `/reset` - Hapus transaksi (bisa pilih tanggal)

*4️⃣ Fitur Otomatis*
• 📸 Kirim foto bukti transfer untuk OCR
• ⏰ Rekap otomatis jam 23:00 (Draft) & 02:00 (Final)
• 💾 Data tersimpan aman + riwayat perubahan
• 📊 Total selisih di rekap mingguan/bulanan

_Gunakan tombol di bawah untuk navigasi cepat_
"""
        keyboard = [[InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def mingguan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /mingguan - rekap 7 hari terakhir"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=6)

            summaries = self.storage.get_summaries_range(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            if not summaries:
                await update.message.reply_text(
                    "📭 *Rekap Mingguan*\n\n"
                    "Belum ada data rekap tersimpan dalam 7 hari terakhir.\n\n"
                    "💡 Rekap otomatis dibuat:\n"
                    "• Jam 23:00 → DRAFT\n"
                    "• Jam 02:00 → FINAL",
                    parse_mode='Markdown'
                )
                return

            # Calculate totals
            total_omzet = sum(s[13] for s in summaries)  # omzet_manual
            total_tf = sum(s[6] for s in summaries)      # total_tf
            total_keluar = sum(s[8] for s in summaries)  # total_pengeluaran
            total_pos = sum(s[10] for s in summaries)    # pos_total
            # Total selisih (index 14) - minus dikurangi, plus ditambah
            total_selisih = sum(s[14] for s in summaries)  # selisih
            days_plus = sum(1 for s in summaries if s[14] > 0)
            days_minus = sum(1 for s in summaries if s[14] < 0)

            # Format selisih dengan tanda
            selisih_str = f"+{format_rupiah(total_selisih)}" if total_selisih >= 0 else format_rupiah(total_selisih)

            message = f"""
📅 *REKAP MINGGUAN*
{start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━
📊 RINGKASAN
━━━━━━━━━━━━━━━━━━━━━━━━
📈 Total Omzet Manual: {format_rupiah(total_omzet)}
🖥️ Total Omzet POS: {format_rupiah(total_pos)}
💳 Total Transfer: {format_rupiah(total_tf)}
📤 Total Pengeluaran: {format_rupiah(total_keluar)}
📊 Rata-rata/hari: {format_rupiah(total_omzet // len(summaries) if summaries else 0)}

━━━━━━━━━━━━━━━━━━━━━━━━
📉 TOTAL SELISIH
━━━━━━━━━━━━━━━━━━━━━━━━
📊 Total: {selisih_str}
📈 Hari Plus: {days_plus} hari
📉 Hari Minus: {days_minus} hari

━━━━━━━━━━━━━━━━━━━━━━━━
📋 DETAIL PER HARI
━━━━━━━━━━━━━━━━━━━━━━━━
"""
            for s in summaries:
                date = s[1]
                state = s[3]
                omzet = s[13]
                selisih = s[14]
                status_icon = s[17]
                version = s[2]

                state_label = {'DRAFT': '📝', 'FINAL': '✅', 'REVISED': '🔄'}.get(state, '❓')
                v_label = f"v{version}" if version > 1 else ""
                selisih_sign = f"+{format_rupiah(selisih)}" if selisih >= 0 else format_rupiah(selisih)

                message += f"{date}: {format_rupiah(omzet)} | {selisih_sign} {status_icon} {state_label}{v_label}\n"

            message += f"\n📊 Data: {len(summaries)} hari tercatat"

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in mingguan_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def bulanan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /bulanan - rekap bulan ini"""
        try:
            now = datetime.now()
            start_date = now.replace(day=1)

            summaries = self.storage.get_summaries_range(
                start_date.strftime('%Y-%m-%d'),
                now.strftime('%Y-%m-%d')
            )

            if not summaries:
                await update.message.reply_text(
                    f"📭 *Rekap Bulanan - {now.strftime('%B %Y')}*\n\n"
                    "Belum ada data rekap tersimpan bulan ini.\n\n"
                    "💡 Rekap otomatis dibuat:\n"
                    "• Jam 23:00 → DRAFT\n"
                    "• Jam 02:00 → FINAL",
                    parse_mode='Markdown'
                )
                return

            # Calculate totals
            total_omzet = sum(s[13] for s in summaries)
            total_tf = sum(s[6] for s in summaries)
            total_keluar = sum(s[8] for s in summaries)
            total_pos = sum(s[10] for s in summaries)
            # Total selisih (index 14) - minus dikurangi, plus ditambah
            total_selisih = sum(s[14] for s in summaries)  # selisih
            days_plus = sum(1 for s in summaries if s[14] > 0)
            days_minus = sum(1 for s in summaries if s[14] < 0)

            # Format selisih dengan tanda
            selisih_str = f"+{format_rupiah(total_selisih)}" if total_selisih >= 0 else format_rupiah(total_selisih)

            message = f"""
📆 *REKAP BULANAN*
{now.strftime('%B %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━
📊 RINGKASAN
━━━━━━━━━━━━━━━━━━━━━━━━
📈 Total Omzet Manual: {format_rupiah(total_omzet)}
🖥️ Total Omzet POS: {format_rupiah(total_pos)}
💳 Total Transfer: {format_rupiah(total_tf)}
📤 Total Pengeluaran: {format_rupiah(total_keluar)}
📊 Rata-rata/hari: {format_rupiah(total_omzet // len(summaries) if summaries else 0)}

━━━━━━━━━━━━━━━━━━━━━━━━
📉 TOTAL SELISIH
━━━━━━━━━━━━━━━━━━━━━━━━
📊 Total: {selisih_str}
📈 Hari Plus: {days_plus} hari
📉 Hari Minus: {days_minus} hari

━━━━━━━━━━━━━━━━━━━━━━━━
📋 DATA
━━━━━━━━━━━━━━━━━━━━━━━━
📊 Hari Tercatat: {len(summaries)} hari
📅 Periode: {start_date.strftime('%d %b')} - {now.strftime('%d %b %Y')}
"""

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in bulanan_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def text_input_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk text input dari button flow (state machine)"""
        # Check if there's a pending input from button flow
        pending_input = context.user_data.get('pending_input')
        pending_addtx = context.user_data.get('pending_addtx')

        if not pending_input and not pending_addtx:
            return  # No pending input, let it pass to other handlers

        try:
            text = update.message.text.strip()
            amount = parse_amount(text)

            if amount <= 0:
                await update.message.reply_text("❌ Jumlah harus > 0")
                return

            # Handle adding transaction to past date
            if pending_addtx:
                date_str = pending_addtx['date']
                tipe = pending_addtx['tipe']
                username = self._get_username(update.effective_user)
                waktu = datetime.now().strftime('%H:%M:%S')

                tx_id = self.storage.add_transaction(
                    tanggal=date_str,
                    waktu=waktu,
                    tipe=tipe,
                    jumlah=amount,
                    sumber='button_editrekap',
                    keterangan=f'Ditambahkan via button oleh {username}',
                    chat_id=update.effective_chat.id,
                    user_id=update.effective_user.id,
                    username=username,
                    message_id=update.message.message_id
                )

                # Auto-generate REVISED summary
                summary_data = self.logic.calculate_daily_summary(date_str)
                self.storage.save_daily_summary(
                    date=date_str,
                    state='REVISED',
                    summary_data=summary_data,
                    notes=f'Revisi: {tipe} {amount} ditambahkan via button oleh {username}'
                )

                context.user_data.pop('pending_addtx', None)

                tipe_names = {'modal': 'Modal', 'cash': 'Cash', 'tf': 'Transfer', 'keluar': 'Pengeluaran', 'pos': 'Total POS'}
                await update.message.reply_text(
                    f"✅ {tipe_names.get(tipe, tipe)} {format_rupiah(amount)} ditambahkan\n"
                    f"📅 Tanggal: {date_str}\n"
                    f"🔑 ID: {tx_id}\n"
                    f"🔄 Rekap direvisi otomatis"
                )
                logger.info(f"AddTx via button: {tipe}={amount}, date={date_str} by {username}")
                return

            # Handle regular pending input (for today)
            if pending_input:
                tanggal = datetime.now().strftime('%Y-%m-%d')
                waktu = datetime.now().strftime('%H:%M:%S')

                # Map input type to transaction type
                type_map = {
                    'cash': 'cash',
                    'tf': 'tf',
                    'keluar': 'keluar',
                    'modal': 'modal',
                    'pos': 'pos'
                }
                tipe = type_map.get(pending_input, pending_input)

                # Save transaction
                self.storage.add_transaction(
                    tanggal=tanggal,
                    waktu=waktu,
                    tipe=tipe,
                    jumlah=amount,
                    sumber='button',
                    keterangan='',
                    chat_id=update.effective_chat.id,
                    user_id=update.effective_user.id,
                    username=self._get_username(update.effective_user),
                    message_id=update.message.message_id
                )

                # Clear pending state
                context.user_data.pop('pending_input', None)

                type_names = {
                    'cash': 'Cash akhir',
                    'tf': 'Transfer/QRIS',
                    'keluar': 'Pengeluaran',
                    'modal': 'Modal awal',
                    'pos': 'Total POS'
                }
                name = type_names.get(tipe, 'Transaksi')

                await update.message.reply_text(f"✅ {name} {format_rupiah(amount)} tersimpan")
                logger.info(f"{tipe} via button: {amount}")

        except ValueError as e:
            await update.message.reply_text(f"❌ Format tidak valid: {str(e)}")
        except Exception as e:
            logger.error(f"Error in text_input_handler: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")
            context.user_data.pop('pending_input', None)

    async def editrekap_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /editrekap [YYYY-MM-DD] - edit transaksi tanggal lalu"""
        try:
            import re as regex

            # Parse tanggal dari argumen atau tampilkan help
            if not context.args:
                await update.message.reply_text(
                    "📝 *EDIT REKAP*\n\n"
                    "Gunakan format:\n"
                    "• `/editrekap TANGGAL` - lihat transaksi\n"
                    "• `/editrekap TANGGAL tambah TIPE JUMLAH` - tambah baru\n"
                    "• `/editrekap TANGGAL hapus ID` - hapus transaksi\n"
                    "• `/editrekap TANGGAL ID JUMLAH` - ubah jumlah\n\n"
                    "*Contoh:*\n"
                    "• `/editrekap 2025-12-20`\n"
                    "• `/editrekap 2025-12-20 tambah pos 1.5jt`\n"
                    "• `/editrekap 2025-12-20 tambah tf 300k`\n"
                    "• `/editrekap 2025-12-20 hapus 123`\n"
                    "• `/editrekap 2025-12-20 123 150k`\n\n"
                    "_TIPE: modal, cash, tf, keluar, pos_",
                    parse_mode='Markdown'
                )
                return

            date_str = context.args[0]

            # Validasi format tanggal
            if not regex.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                await update.message.reply_text(
                    "❌ Format tanggal salah.\n\n"
                    "Gunakan format: `/editrekap YYYY-MM-DD`\n"
                    "Contoh: `/editrekap 2025-12-20`",
                    parse_mode='Markdown'
                )
                return

            # Jika hanya tanggal, tampilkan transaksi untuk tanggal tersebut
            if len(context.args) == 1:
                transactions = self.storage.get_transactions_by_date(date_str)

                message = f"📝 *EDIT REKAP*\n📅 {date_str}\n\n"

                if not transactions:
                    message += "📭 _Belum ada transaksi_\n\n"
                else:
                    tipe_emoji = {'modal': '💰', 'cash': '💵', 'tf': '💳', 'keluar': '📤', 'pos': '🖥️'}
                    tipe_label = {'modal': 'MODAL', 'cash': 'CASH', 'tf': 'TF', 'keluar': 'KELUAR', 'pos': 'POS'}

                    for i, tx in enumerate(transactions, 1):
                        tx_id = tx[0]
                        waktu = tx[2][:5]
                        tipe = tx[3]
                        jumlah = tx[4]
                        ket = tx[6] if tx[6] else ''

                        emoji = tipe_emoji.get(tipe, '📝')
                        label = tipe_label.get(tipe, tipe.upper())

                        line = f"{i}. [{waktu}] {emoji} {label}: {format_rupiah(jumlah)}"
                        if ket:
                            line += f"\n   💬 {ket}"
                        line += f"\n   🔑 ID: `{tx_id}`\n"

                        message += line

                message += f"\n📝 *Aksi:*\n"
                message += f"➕ Tambah: `/editrekap {date_str} tambah pos 1.5jt`\n"
                message += f"🗑️ Hapus: `/editrekap {date_str} hapus ID`\n"
                message += f"✏️ Ubah: `/editrekap {date_str} ID JUMLAH`\n"

                await update.message.reply_text(message, parse_mode='Markdown')
                return

            # Action: tambah transaksi baru
            if context.args[1].lower() == 'tambah':
                if len(context.args) < 4:
                    await update.message.reply_text(
                        "❌ Format: `/editrekap TANGGAL tambah TIPE JUMLAH`\n\n"
                        "TIPE: `modal`, `cash`, `tf`, `keluar`, `pos`\n\n"
                        "Contoh:\n"
                        "• `/editrekap 2025-12-20 tambah pos 1.5jt`\n"
                        "• `/editrekap 2025-12-20 tambah tf 300k`",
                        parse_mode='Markdown'
                    )
                    return

                tipe = context.args[2].lower()
                valid_types = ['modal', 'cash', 'tf', 'keluar', 'pos']
                if tipe not in valid_types:
                    await update.message.reply_text(
                        f"❌ Tipe `{tipe}` tidak valid.\n\n"
                        f"Gunakan: `modal`, `cash`, `tf`, `keluar`, `pos`",
                        parse_mode='Markdown'
                    )
                    return

                amount_str = ' '.join(context.args[3:])
                try:
                    amount = parse_amount(amount_str)
                except ValueError as e:
                    await update.message.reply_text(f"❌ Format jumlah tidak valid: {str(e)}")
                    return

                if amount < 0:
                    await update.message.reply_text("❌ Jumlah tidak boleh negatif")
                    return

                username = self._get_username(update.effective_user)
                waktu = datetime.now().strftime('%H:%M:%S')

                # Tambah transaksi
                tx_id = self.storage.add_transaction(
                    tanggal=date_str,
                    waktu=waktu,
                    tipe=tipe,
                    jumlah=amount,
                    sumber='editrekap',
                    keterangan=f'Ditambahkan via editrekap oleh {username}',
                    chat_id=update.effective_chat.id,
                    user_id=update.effective_user.id,
                    username=username,
                    message_id=update.message.message_id
                )

                # Auto-generate REVISED summary
                summary_data = self.logic.calculate_daily_summary(date_str)
                self.storage.save_daily_summary(
                    date=date_str,
                    state='REVISED',
                    summary_data=summary_data,
                    notes=f'Revisi: {tipe} {amount} ditambahkan oleh {username}'
                )

                tipe_names = {'modal': 'Modal', 'cash': 'Cash', 'tf': 'Transfer', 'keluar': 'Pengeluaran', 'pos': 'Total POS'}
                await update.message.reply_text(
                    f"✅ {tipe_names.get(tipe, tipe)} {format_rupiah(amount)} ditambahkan\n"
                    f"📅 Tanggal: {date_str}\n"
                    f"🔑 ID: {tx_id}\n"
                    f"🔄 Rekap direvisi otomatis"
                )
                logger.info(f"EditRekap ADD: {tipe}={amount}, date={date_str} by {username}")
                return

            # Action: hapus
            if context.args[1].lower() == 'hapus':
                if len(context.args) < 3:
                    await update.message.reply_text("❌ Format: `/editrekap TANGGAL hapus ID`", parse_mode='Markdown')
                    return

                try:
                    tx_id = int(context.args[2])
                except ValueError:
                    await update.message.reply_text("❌ ID harus berupa angka")
                    return

                # Verifikasi transaksi ada dan sesuai tanggal
                tx = self.storage.get_transaction_by_id(tx_id)
                if not tx:
                    await update.message.reply_text(f"❌ Transaksi ID {tx_id} tidak ditemukan")
                    return
                if tx[1] != date_str:
                    await update.message.reply_text(f"❌ Transaksi ID {tx_id} bukan untuk tanggal {date_str}")
                    return

                username = self._get_username(update.effective_user)
                self.storage.delete_transaction(tx_id, username=username)

                # Auto-generate REVISED summary
                summary_data = self.logic.calculate_daily_summary(date_str)
                self.storage.save_daily_summary(
                    date=date_str,
                    state='REVISED',
                    summary_data=summary_data,
                    notes=f'Revisi: transaksi ID {tx_id} dihapus oleh {username}'
                )

                await update.message.reply_text(
                    f"✅ Transaksi ID {tx_id} berhasil dihapus\n"
                    f"🔄 Rekap {date_str} direvisi otomatis"
                )
                logger.info(f"EditRekap DELETE: ID={tx_id}, date={date_str} by {username}")
                return

            # Action: ubah jumlah
            try:
                tx_id = int(context.args[1])
            except ValueError:
                await update.message.reply_text("❌ ID harus berupa angka\nFormat: `/editrekap TANGGAL ID JUMLAH`", parse_mode='Markdown')
                return

            if len(context.args) < 3:
                await update.message.reply_text("❌ Format: `/editrekap TANGGAL ID JUMLAH`", parse_mode='Markdown')
                return

            # Verifikasi transaksi ada dan sesuai tanggal
            tx = self.storage.get_transaction_by_id(tx_id)
            if not tx:
                await update.message.reply_text(f"❌ Transaksi ID {tx_id} tidak ditemukan")
                return
            if tx[1] != date_str:
                await update.message.reply_text(f"❌ Transaksi ID {tx_id} bukan untuk tanggal {date_str}")
                return

            amount_str = ' '.join(context.args[2:])
            try:
                new_amount = parse_amount(amount_str)
            except ValueError as e:
                await update.message.reply_text(f"❌ Format jumlah tidak valid: {str(e)}")
                return

            if new_amount < 0:
                await update.message.reply_text("❌ Jumlah tidak boleh negatif")
                return

            username = self._get_username(update.effective_user)
            old_amount = tx[4]
            self.storage.update_transaction(tx_id, username=username, jumlah=new_amount)

            # Auto-generate REVISED summary
            summary_data = self.logic.calculate_daily_summary(date_str)
            self.storage.save_daily_summary(
                date=date_str,
                state='REVISED',
                summary_data=summary_data,
                notes=f'Revisi: ID {tx_id} diubah {old_amount} → {new_amount} oleh {username}'
            )

            await update.message.reply_text(
                f"✅ Transaksi ID {tx_id} diubah\n"
                f"💵 {format_rupiah(old_amount)} → {format_rupiah(new_amount)}\n"
                f"🔄 Rekap {date_str} direvisi otomatis"
            )
            logger.info(f"EditRekap UPDATE: ID={tx_id}, {old_amount} → {new_amount} by {username}")

        except Exception as e:
            logger.error(f"Error in editrekap_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    async def riwayat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /riwayat [YYYY-MM-DD] - lihat riwayat perubahan"""
        try:
            import re as regex

            # Default ke hari ini jika tidak ada argumen
            if context.args:
                date_str = context.args[0]
                # Validasi format tanggal
                if not regex.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                    await update.message.reply_text(
                        "❌ Format tanggal salah.\n\n"
                        "Gunakan format: `/riwayat YYYY-MM-DD`\n"
                        "Contoh: `/riwayat 2025-12-20`",
                        parse_mode='Markdown'
                    )
                    return
            else:
                date_str = datetime.now().strftime('%Y-%m-%d')

            # Ambil audit log untuk tanggal tersebut
            logs = self.storage.get_audit_log_by_date(date_str)

            if not logs:
                await update.message.reply_text(
                    f"📭 *RIWAYAT PERUBAHAN*\n\n"
                    f"📅 {date_str}\n\n"
                    f"Belum ada log perubahan untuk tanggal ini.",
                    parse_mode='Markdown'
                )
                return

            message = f"📜 *RIWAYAT PERUBAHAN*\n📅 {date_str}\n\n"

            action_emoji = {'ADD': '➕', 'EDIT': '✏️', 'DELETE': '🗑️'}
            action_label = {'ADD': 'Tambah', 'EDIT': 'Edit', 'DELETE': 'Hapus'}

            for log in logs[:20]:  # Limit 20 entries
                log_id, timestamp, action, entity_type, entity_id, entity_date, username, field, old_val, new_val, notes = log

                # Parse timestamp
                try:
                    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = ts.strftime('%H:%M')
                except:
                    time_str = timestamp[:5] if timestamp else '??:??'

                emoji = action_emoji.get(action, '📝')
                label = action_label.get(action, action)

                line = f"{emoji} [{time_str}] *{label}* oleh {username}\n"

                if action == 'ADD':
                    line += f"   📋 {field}: {format_rupiah(float(new_val)) if new_val else '-'}\n"
                elif action == 'EDIT':
                    if old_val and new_val:
                        try:
                            line += f"   📋 {field}: {format_rupiah(float(old_val))} → {format_rupiah(float(new_val))}\n"
                        except:
                            line += f"   📋 {field}: {old_val} → {new_val}\n"
                elif action == 'DELETE':
                    line += f"   📋 {field}: {format_rupiah(float(old_val)) if old_val else '-'} dihapus\n"

                if notes:
                    line += f"   💬 {notes}\n"

                message += line

            if len(logs) > 20:
                message += f"\n_...dan {len(logs) - 20} log lainnya_\n"

            message += f"\n📊 Total: {len(logs)} perubahan"

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in riwayat_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan")

    def run(self):
        """Jalankan bot"""
        application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()

        # Register handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("menu", self.menu_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("modal", self.modal_command))
        application.add_handler(CommandHandler("cash", self.cash_command))
        application.add_handler(CommandHandler("tf", self.tf_command))
        application.add_handler(CommandHandler("keluar", self.keluar_command))
        application.add_handler(CommandHandler("totalpos", self.totalpos_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("lihat", self.lihat_command))
        application.add_handler(CommandHandler("edit", self.edit_command))
        application.add_handler(CommandHandler("reset", self.reset_command))
        application.add_handler(CommandHandler("mingguan", self.mingguan_command))
        application.add_handler(CommandHandler("bulanan", self.bulanan_command))
        application.add_handler(CommandHandler("editrekap", self.editrekap_command))
        application.add_handler(CommandHandler("riwayat", self.riwayat_command))

        application.add_handler(MessageHandler(filters.PHOTO, self.photo_handler))
        # Text handler for button flow (must be after command handlers)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_input_handler))
        application.add_handler(CallbackQueryHandler(self.callback_query_handler))

        # Start scheduler after event loop is running (via post_init)
        async def start_scheduler(app):
            self.scheduler.start()
            logger.info("Scheduler started: DRAFT at 23:00, FINAL at 02:00")

        application.post_init = start_scheduler

        logger.info("Asisten Keuangan Anisa Store v2 starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    bot = TokoBot()
    bot.run()
