"""
Scheduler untuk generate rekap harian otomatis
- 23:00 → DRAFT (hari ini)
- 02:00 → FINAL (kemarin, with grace period)

Diintegrasikan ke dalam bot.py process yang sama.
"""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

if TYPE_CHECKING:
    from storage import Storage
    from logic import FinancialLogic

logger = logging.getLogger(__name__)


class RekapScheduler:
    """
    Scheduler untuk otomatis generate rekap harian.

    - DRAFT jam 23:00: snapshot hari ini, masih bisa dikoreksi
    - FINAL jam 02:00: finalisasi kemarin (after grace period)
    """

    def __init__(self, storage: 'Storage', logic: 'FinancialLogic', timezone: str = "Asia/Jakarta"):
        self.storage = storage
        self.logic = logic
        self.timezone = timezone
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self._is_running = False

    def start(self):
        """
        Start scheduler dengan dua job:
        1. DRAFT setiap hari jam 23:00
        2. FINAL setiap hari jam 02:00 (untuk tanggal kemarin)
        """
        if self._is_running:
            logger.warning("Scheduler already running")
            return

        # Job 1: Generate DRAFT jam 23:00 WIB
        self.scheduler.add_job(
            self.generate_draft,
            CronTrigger(hour=23, minute=0, timezone=self.timezone),
            id='daily_draft',
            name='Generate Daily Draft at 23:00',
            replace_existing=True
        )

        # Job 2: Generate FINAL jam 02:00 WIB (untuk kemarin)
        self.scheduler.add_job(
            self.generate_final,
            CronTrigger(hour=2, minute=0, timezone=self.timezone),
            id='daily_final',
            name='Generate Daily Final at 02:00',
            replace_existing=True
        )

        self.scheduler.start()
        self._is_running = True
        logger.info(f"RekapScheduler started with timezone {self.timezone}")
        logger.info("  - DRAFT: every day at 23:00")
        logger.info("  - FINAL: every day at 02:00 (for previous day)")

    def stop(self):
        """Stop scheduler gracefully"""
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("RekapScheduler stopped")

    async def generate_draft(self, target_date: str = None):
        """
        Generate DRAFT rekap untuk hari ini (atau target_date jika specified).
        Dipanggil otomatis jam 23:00 atau manual via trigger.
        """
        try:
            if target_date is None:
                target_date = datetime.now().strftime('%Y-%m-%d')

            logger.info(f"Generating DRAFT for {target_date}")

            # Hitung summary dari transaksi
            summary_data = self.logic.calculate_daily_summary(target_date)

            # Cek apakah ada data transaksi
            if summary_data['modal'] == 0 and summary_data['pos_total'] == 0:
                logger.info(f"No transactions for {target_date}, skipping DRAFT")
                return None

            # Simpan sebagai DRAFT
            summary_id = self.storage.save_daily_summary(
                date=target_date,
                state='DRAFT',
                summary_data=summary_data,
                notes='Auto-generated draft at 23:00'
            )

            logger.info(f"DRAFT saved for {target_date}, ID={summary_id}")
            return summary_id

        except Exception as e:
            logger.error(f"Error generating DRAFT for {target_date}: {e}")
            return None

    async def generate_final(self, target_date: str = None):
        """
        Generate FINAL rekap untuk kemarin (atau target_date jika specified).
        Dipanggil otomatis jam 02:00.

        PENTING: Jam 02:00 itu untuk FINALISASI KEMARIN, bukan hari ini!
        """
        try:
            if target_date is None:
                # FINAL jam 02:00 adalah untuk KEMARIN
                yesterday = datetime.now() - timedelta(days=1)
                target_date = yesterday.strftime('%Y-%m-%d')

            logger.info(f"Generating FINAL for {target_date}")

            # Hitung summary dari transaksi (mungkin ada update malam)
            summary_data = self.logic.calculate_daily_summary(target_date)

            # Cek apakah ada data transaksi
            if summary_data['modal'] == 0 and summary_data['pos_total'] == 0:
                logger.info(f"No transactions for {target_date}, skipping FINAL")
                return None

            # Simpan sebagai FINAL
            summary_id = self.storage.save_daily_summary(
                date=target_date,
                state='FINAL',
                summary_data=summary_data,
                notes='Auto-generated final at 02:00'
            )

            logger.info(f"FINAL saved for {target_date}, ID={summary_id}")
            return summary_id

        except Exception as e:
            logger.error(f"Error generating FINAL for {target_date}: {e}")
            return None

    async def generate_revised(self, target_date: str, notes: str = None):
        """
        Generate REVISED rekap untuk tanggal tertentu.
        Dipanggil setelah ada reset atau koreksi transaksi.

        Args:
            target_date: Tanggal yang direvisi (YYYY-MM-DD)
            notes: Catatan alasan revisi
        """
        try:
            logger.info(f"Generating REVISED for {target_date}")

            # Hitung summary dari transaksi terkini
            summary_data = self.logic.calculate_daily_summary(target_date)

            # Simpan sebagai REVISED
            summary_id = self.storage.save_daily_summary(
                date=target_date,
                state='REVISED',
                summary_data=summary_data,
                notes=notes or 'Manual revision after correction'
            )

            logger.info(f"REVISED saved for {target_date}, ID={summary_id}")
            return summary_id

        except Exception as e:
            logger.error(f"Error generating REVISED for {target_date}: {e}")
            return None

    def trigger_draft_now(self, target_date: str = None):
        """
        Trigger DRAFT generation secara manual (untuk testing).
        Returns coroutine yang harus di-await.
        """
        return self.generate_draft(target_date)

    def trigger_final_now(self, target_date: str = None):
        """
        Trigger FINAL generation secara manual (untuk testing).
        Returns coroutine yang harus di-await.
        """
        return self.generate_final(target_date)

    def get_scheduled_jobs(self):
        """Get list of scheduled jobs for debugging"""
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run': str(job.next_run_time) if job.next_run_time else None
            }
            for job in self.scheduler.get_jobs()
        ]
