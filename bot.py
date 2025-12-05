"""
Telegram Bot untuk Pencatatan Keuangan Harian Toko
Entry point utama bot
"""

import logging
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
from datetime import datetime
import asyncio

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

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk command /start"""
        welcome_message = """
🏪 *Bot Pencatatan Keuangan Toko*

Perintah yang tersedia:
• /modal <jumlah> - Catat modal awal hari ini
• /cash <jumlah> - Catat cash akhir di laci
• /tf <jumlah> - Catat transfer/QRIS masuk
• /keluar <jumlah> [keterangan] - Catat pengeluaran
• /totalpos <jumlah> - Input total omzet POS
• /status - Lihat status keuangan hari ini
• /lihat - Lihat transaksi hari ini

Format angka yang didukung:
• 4000, 4k, 4K, 4rb, 4.000, 4,000, 4jt, dll
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def modal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /modal <amount>"""
        try:
            if not context.args:
                await update.message.reply_text("❌ Format: /modal <jumlah>\nContoh: /modal 500000")
                return

            amount_str = ' '.join(context.args)
            amount = parse_amount(amount_str)

            if amount <= 0:
                await update.message.reply_text("❌ Jumlah harus lebih dari 0")
                return

            # Simpan transaksi
            tanggal = datetime.now().strftime('%Y-%m-%d')
            waktu = datetime.now().strftime('%H:%M:%S')

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
                f"✅ Modal awal {format_rupiah(amount)} untuk tanggal {tanggal} tersimpan."
            )
            logger.info(f"Modal saved: {amount} by user {update.effective_user.id}")

        except ValueError as e:
            await update.message.reply_text(f"❌ Format angka tidak valid: {str(e)}")
        except Exception as e:
            logger.error(f"Error in modal_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan saat menyimpan modal")

    async def cash_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /cash <amount>"""
        try:
            if not context.args:
                await update.message.reply_text("❌ Format: /cash <jumlah>\nContoh: /cash 1200000")
                return

            amount_str = ' '.join(context.args)
            amount = parse_amount(amount_str)

            if amount < 0:
                await update.message.reply_text("❌ Jumlah tidak boleh negatif")
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

            await update.message.reply_text(
                f"✅ Cash akhir {format_rupiah(amount)} tersimpan untuk hari ini."
            )
            logger.info(f"Cash saved: {amount} by user {update.effective_user.id}")

        except ValueError as e:
            await update.message.reply_text(f"❌ Format angka tidak valid: {str(e)}")
        except Exception as e:
            logger.error(f"Error in cash_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan saat menyimpan cash")

    async def tf_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /tf <amount>"""
        try:
            if not context.args:
                await update.message.reply_text("❌ Format: /tf <jumlah>\nContoh: /tf 800000")
                return

            amount_str = ' '.join(context.args)
            amount = parse_amount(amount_str)

            if amount <= 0:
                await update.message.reply_text("❌ Jumlah harus lebih dari 0")
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

            await update.message.reply_text(
                f"✅ Transfer/QRIS {format_rupiah(amount)} tercatat."
            )
            logger.info(f"TF saved: {amount} by user {update.effective_user.id}")

        except ValueError as e:
            await update.message.reply_text(f"❌ Format angka tidak valid: {str(e)}")
        except Exception as e:
            logger.error(f"Error in tf_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan saat menyimpan transfer")

    async def keluar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /keluar <amount> [keterangan]"""
        try:
            if not context.args:
                await update.message.reply_text("❌ Format: /keluar <jumlah> [keterangan]\nContoh: /keluar 200000 beli gas")
                return

            # Parse jumlah (ambil kata pertama)
            amount = parse_amount(context.args[0])

            # Parse keterangan (sisa kata)
            keterangan = ' '.join(context.args[1:]) if len(context.args) > 1 else ''

            if amount <= 0:
                await update.message.reply_text("❌ Jumlah harus lebih dari 0")
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

            msg = f"✅ Pengeluaran {format_rupiah(amount)} tercatat."
            if keterangan:
                msg += f" ({keterangan})"

            await update.message.reply_text(msg)
            logger.info(f"Pengeluaran saved: {amount} by user {update.effective_user.id}")

        except ValueError as e:
            await update.message.reply_text(f"❌ Format angka tidak valid: {str(e)}")
        except Exception as e:
            logger.error(f"Error in keluar_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan saat menyimpan pengeluaran")

    async def totalpos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /totalpos <amount>"""
        try:
            if not context.args:
                await update.message.reply_text("❌ Format: /totalpos <jumlah>\nContoh: /totalpos 2100000")
                return

            amount_str = ' '.join(context.args)
            amount = parse_amount(amount_str)

            if amount < 0:
                await update.message.reply_text("❌ Jumlah tidak boleh negatif")
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

            await update.message.reply_text(
                f"✅ Total POS hari ini {format_rupiah(amount)} tersimpan (menggantikan jika sebelumnya sudah ada)."
            )
            logger.info(f"POS total saved: {amount} by user {update.effective_user.id}")

        except ValueError as e:
            await update.message.reply_text(f"❌ Format angka tidak valid: {str(e)}")
        except Exception as e:
            logger.error(f"Error in totalpos_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan saat menyimpan total POS")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /status - menampilkan rekap keuangan hari ini"""
        try:
            tanggal = datetime.now().strftime('%Y-%m-%d')
            tanggal_display = datetime.now().strftime('%A, %d %B %Y')

            # Gunakan locale Indonesia jika tersedia (fallback ke default)
            try:
                import locale
                locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
                tanggal_display = datetime.now().strftime('%A, %d %B %Y')
            except:
                pass  # Gunakan format default jika locale tidak tersedia

            summary = self.logic.calculate_daily_summary(tanggal)

            # Format output sesuai spesifikasi
            message = f"""📊 *STATUS HARI INI*
📅 {tanggal_display}

💰 Modal Awal: {format_rupiah(summary['modal'])}
💵 Cash Akhir (di laci): {format_rupiah(summary['cash_akhir'])}
💳 Total TF/QRIS: {format_rupiah(summary['total_tf'])}
📤 Total Pengeluaran: {format_rupiah(summary['total_pengeluaran'])}

📈 Penjualan Cash Manual (C - M + E): {format_rupiah(summary['penjualan_cash'])}
📈 Omzet Manual (C - M + E + T): {format_rupiah(summary['omzet_manual'])}

🖥️ Omzet POS: {format_rupiah(summary['pos_total'])}
📊 Selisih (Manual - POS): {format_rupiah(summary['selisih'])} ({summary['selisih_persen']:.2f}%)

{summary['status_icon']} {summary['status_text']}"""

            await update.message.reply_text(message, parse_mode='Markdown')
            logger.info(f"Status requested by user {update.effective_user.id}")

        except Exception as e:
            logger.error(f"Error in status_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan saat menghitung status")

    async def lihat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /lihat - menampilkan list transaksi hari ini"""
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

            message = f"📒 *DATA TRANSAKSI HARI INI*\n📅 {tanggal_display}\n\n"

            if not transactions:
                message += "_Belum ada transaksi hari ini_\n\n"
            else:
                tipe_emoji = {
                    'modal': '💰 MODAL',
                    'cash': '💵 CASH',
                    'tf': '💳 TF',
                    'keluar': '📤 KELUAR',
                    'pos': '🖥️ POS'
                }

                for i, tx in enumerate(transactions, 1):
                    waktu = tx[2]  # waktu dari tuple result
                    tipe = tx[3]
                    jumlah = tx[4]
                    keterangan = tx[6] if tx[6] else ''

                    tipe_label = tipe_emoji.get(tipe, tipe.upper())
                    line = f"{i}) [{waktu}] {tipe_label} {format_rupiah(jumlah)}"
                    if keterangan:
                        line += f" - {keterangan}"
                    message += line + "\n"

            # Tambahkan summary
            message += f"""
💰 Modal Awal: {format_rupiah(summary['modal'])}
💵 Cash Akhir: {format_rupiah(summary['cash_akhir'])}
💳 Total TF/QRIS: {format_rupiah(summary['total_tf'])}
📤 Total Pengeluaran: {format_rupiah(summary['total_pengeluaran'])}
📈 Omzet Manual: {format_rupiah(summary['omzet_manual'])}
🖥️ Omzet POS: {format_rupiah(summary['pos_total'])}
📊 Selisih: {format_rupiah(summary['selisih'])} ({summary['selisih_persen']:.2f}%)"""

            await update.message.reply_text(message, parse_mode='Markdown')
            logger.info(f"Lihat requested by user {update.effective_user.id}")

        except Exception as e:
            logger.error(f"Error in lihat_command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan saat mengambil data transaksi")

    async def photo_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler untuk foto yang dikirim dengan caption 'tf' atau 'transfer'
        TODO: Integrate dengan n8n OCR service
        """
        try:
            caption = update.message.caption if update.message.caption else ''
            caption_lower = caption.lower().strip()

            # Cek apakah caption mengandung kata kunci tf/transfer
            if 'tf' not in caption_lower and 'transfer' not in caption_lower:
                return  # Abaikan foto tanpa keyword

            # Ambil file_id foto terbesar (kualitas tertinggi)
            photo = update.message.photo[-1]
            file_id = photo.file_id

            # TODO: Implementasi OCR call ke n8n
            # Untuk sekarang, kirim notifikasi bahwa fitur OCR belum aktif
            await update.message.reply_text(
                "📷 Foto bukti transfer diterima.\n"
                "⚠️ Fitur OCR otomatis belum aktif. Silakan gunakan /tf <jumlah> untuk mencatat manual."
            )

            logger.info(f"Photo received with caption '{caption}' from user {update.effective_user.id}")

            # STUB: Fungsi untuk mengirim ke n8n (belum diimplementasi)
            # await self.send_to_ocr_service(file_id, caption, update.effective_chat.id, update.message.message_id)

        except Exception as e:
            logger.error(f"Error in photo_handler: {e}")

    async def send_to_ocr_service(self, file_id: str, caption: str, chat_id: int, message_id: int):
        """
        STUB: Fungsi untuk mengirim foto ke n8n OCR service
        TODO: Implementasi HTTP POST ke N8N_OCR_URL
        """
        # Implementasi akan seperti ini:
        # 1. Download file dari Telegram menggunakan file_id
        # 2. Kirim POST request ke self.config.N8N_OCR_URL dengan payload:
        #    {
        #      "chat_id": chat_id,
        #      "message_id": message_id,
        #      "file_id": file_id,
        #      "note": caption
        #    }
        # 3. N8n akan memproses dan callback ke /ocr-transfer-result
        pass

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk inline button callback (untuk konfirmasi OCR)"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data.startswith('ocr_save_'):
            # Format: ocr_save_AMOUNT_MESSAGEID
            parts = data.split('_')
            if len(parts) >= 4:
                amount = int(parts[2])
                original_msg_id = int(parts[3])

                # Simpan transaksi
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
                    user_id=update.effective_user.id,
                    message_id=original_msg_id
                )

                await query.edit_message_text(
                    f"✅ Transfer {format_rupiah(amount)} dari OCR telah disimpan."
                )
                logger.info(f"OCR transaction saved: {amount}")

        elif data.startswith('ocr_cancel_'):
            await query.edit_message_text("❌ Transaksi OCR dibatalkan.")
            logger.info("OCR transaction cancelled")

    def run(self):
        """Jalankan bot"""
        # Buat application
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

        # Handler untuk foto
        application.add_handler(MessageHandler(filters.PHOTO, self.photo_handler))

        # Handler untuk callback query (inline buttons)
        application.add_handler(CallbackQueryHandler(self.callback_query_handler))

        # Start bot
        logger.info("Bot started...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    bot = TokoBot()
    bot.run()
