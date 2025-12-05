"""
Business logic untuk perhitungan keuangan
PENTING: Rumus dan logika di sini sesuai spesifikasi dan TIDAK BOLEH diubah
"""

from storage import Storage
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class FinancialLogic:
    """Class untuk business logic perhitungan keuangan"""

    def __init__(self, storage: Storage):
        self.storage = storage

        # Threshold untuk status selisih (bisa diambil dari config)
        self.THRESHOLD_SELISIH_KECIL = 1000
        self.THRESHOLD_SELISIH_BESAR = 5000

    def calculate_daily_summary(self, tanggal: str) -> Dict:
        """
        Menghitung summary keuangan harian berdasarkan RUMUS YANG SUDAH DITENTUKAN

        RUMUS (JANGAN DIUBAH):
        1. modal = input terakhir tipe 'modal' untuk tanggal tersebut
        2. totalCash = input terakhir tipe 'cash' untuk tanggal tersebut
        3. totalPengeluaran = SUM semua tipe 'keluar' untuk tanggal tersebut
        4. totalTF = SUM semua tipe 'tf' untuk tanggal tersebut
        5. posTotal = input terakhir tipe 'pos' untuk tanggal tersebut

        6. Penjualan cash manual (S_cash):
           S_cash = totalCash - modal + totalPengeluaran

        7. Omzet manual:
           omzetManual = S_cash + totalTF
                       = totalCash - modal + totalPengeluaran + totalTF

        8. Selisih:
           selisih = omzetManual - posTotal
           selisihAbs = |selisih|
           selisihPersen = (selisihAbs / posTotal * 100) jika posTotal > 0, else 0

        9. Status:
           - Jika posTotal == 0 → "POS BELUM INPUT"
           - Else jika selisihAbs > 5000 → "SELISIH BESAR"
           - Else jika selisihAbs > 1000 → "SELISIH KECIL"
           - Else → "COCOK"

        Returns: Dictionary dengan semua nilai perhitungan
        """

        # 1. Ambil modal (input terakhir)
        modal = self.storage.get_latest_by_type(tanggal, 'modal')
        if modal is None:
            modal = 0.0

        # 2. Ambil cash akhir (input terakhir)
        cash_akhir = self.storage.get_latest_by_type(tanggal, 'cash')
        if cash_akhir is None:
            cash_akhir = 0.0

        # 3. Total pengeluaran (sum semua)
        total_pengeluaran = self.storage.get_sum_by_type(tanggal, 'keluar')

        # 4. Total TF (sum semua)
        total_tf = self.storage.get_sum_by_type(tanggal, 'tf')

        # 5. POS total (input terakhir)
        pos_total = self.storage.get_latest_by_type(tanggal, 'pos')
        if pos_total is None:
            pos_total = 0.0

        # 6. Hitung penjualan cash manual
        # RUMUS: S_cash = totalCash - modal + totalPengeluaran
        penjualan_cash = cash_akhir - modal + total_pengeluaran

        # 7. Hitung omzet manual
        # RUMUS: omzetManual = S_cash + totalTF
        #                    = totalCash - modal + totalPengeluaran + totalTF
        omzet_manual = penjualan_cash + total_tf

        # 8. Hitung selisih
        # RUMUS: selisih = omzetManual - posTotal
        selisih = omzet_manual - pos_total
        selisih_abs = abs(selisih)

        # Hitung persentase selisih
        if pos_total > 0:
            selisih_persen = (selisih_abs / pos_total) * 100
        else:
            selisih_persen = 0.0

        # 9. Tentukan status
        if pos_total == 0:
            status_text = "POS BELUM INPUT"
            status_icon = "⚠️"
        elif selisih_abs > self.THRESHOLD_SELISIH_BESAR:
            status_text = "SELISIH BESAR"
            status_icon = "🚨"
        elif selisih_abs > self.THRESHOLD_SELISIH_KECIL:
            status_text = "SELISIH KECIL"
            status_icon = "⚠️"
        else:
            status_text = "COCOK"
            status_icon = "✅"

        # Log untuk debugging
        logger.info(f"Daily summary calculated for {tanggal}: "
                   f"modal={modal}, cash={cash_akhir}, tf={total_tf}, "
                   f"keluar={total_pengeluaran}, pos={pos_total}, "
                   f"omzet_manual={omzet_manual}, selisih={selisih}")

        return {
            'tanggal': tanggal,
            'modal': modal,
            'cash_akhir': cash_akhir,
            'total_tf': total_tf,
            'total_pengeluaran': total_pengeluaran,
            'pos_total': pos_total,
            'penjualan_cash': penjualan_cash,  # S_cash
            'omzet_manual': omzet_manual,
            'selisih': selisih,  # bisa negatif
            'selisih_abs': selisih_abs,
            'selisih_persen': selisih_persen,
            'status_text': status_text,
            'status_icon': status_icon
        }

    def calculate_weekly_summary(self, start_date: str, end_date: str) -> Dict:
        """
        STUB: Untuk rekap mingguan (future implementation)
        Bisa dipanggil dari n8n atau command /rekapmingguan
        """
        # TODO: Implementasi rekap mingguan
        # - Ambil transaksi dari start_date sampai end_date
        # - Hitung total per kategori
        # - Hitung rata-rata harian
        # - Return summary
        pass

    def calculate_monthly_summary(self, year: int, month: int) -> Dict:
        """
        STUB: Untuk rekap bulanan (future implementation)
        Bisa dipanggil dari n8n atau command /rekapbulanan
        """
        # TODO: Implementasi rekap bulanan
        # - Ambil semua transaksi di bulan tersebut
        # - Group by tanggal
        # - Hitung statistik: total, rata-rata, min, max
        # - Return summary
        pass

    def set_threshold(self, kecil: int = None, besar: int = None):
        """
        Update threshold untuk selisih
        Bisa dipanggil dari config atau command admin
        """
        if kecil is not None:
            self.THRESHOLD_SELISIH_KECIL = kecil
        if besar is not None:
            self.THRESHOLD_SELISIH_BESAR = besar
        logger.info(f"Threshold updated: kecil={self.THRESHOLD_SELISIH_KECIL}, "
                   f"besar={self.THRESHOLD_SELISIH_BESAR}")
