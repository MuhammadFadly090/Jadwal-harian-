import sys
import json
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QFileDialog, QMessageBox
)
from jadwal import Aktivitas, jadwal_optimal
from PyQt5.QtCore import QThread, pyqtSignal, QTimer


class WorkerThread(QThread):
    hasil_selesai = pyqtSignal(dict, float)
    gagal_timeout = pyqtSignal()

    def __init__(self, daftar_aktivitas, total_waktu):
        super().__init__()
        self.daftar_aktivitas = daftar_aktivitas
        self.total_waktu = total_waktu
        self._is_timeout = False

    def run(self):
        start_time = time.perf_counter()
        try:
            hasil = jadwal_optimal(self.daftar_aktivitas, self.total_waktu)
            if self._is_timeout:
                return  # Tidak lakukan apapun jika sudah timeout
            end_time = time.perf_counter()
            elapsed_time = (end_time - start_time) * 1000
            self.hasil_selesai.emit(hasil, elapsed_time)
        except Exception:
            self.gagal_timeout.emit()

    def stop(self):
        self._is_timeout = True
        self.terminate()
        
class App(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Penjadwalan Aktivitas Harian')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.input_nama = QLineEdit(self)
        self.input_nama.setPlaceholderText("Nama Aktivitas")
        layout.addWidget(self.input_nama)

        self.input_durasi = QLineEdit(self)
        self.input_durasi.setPlaceholderText("Durasi (menit)")
        layout.addWidget(self.input_durasi)

        self.input_prioritas = QLineEdit(self)
        self.input_prioritas.setPlaceholderText("Prioritas (1-10)")
        layout.addWidget(self.input_prioritas)

        self.tombol_tambah = QPushButton("Tambah Aktivitas", self)
        self.tombol_tambah.clicked.connect(self.tambah_aktivitas)
        layout.addWidget(self.tombol_tambah)

        self.tombol_import = QPushButton("Import Aktivitas", self)
        self.tombol_import.clicked.connect(self.import_dari_json)
        layout.addWidget(self.tombol_import)

        self.tombol_clear = QPushButton("Clear Aktivitas", self)
        self.tombol_clear.clicked.connect(self.clear_aktivitas)

        layout.addWidget(self.tombol_clear)

        self.table_aktivitas = QTableWidget(self)
        self.table_aktivitas.setColumnCount(3)
        self.table_aktivitas.setHorizontalHeaderLabels(['Nama', 'Durasi', 'Prioritas'])
        layout.addWidget(self.table_aktivitas)

        self.input_waktu = QLineEdit(self)
        self.input_waktu.setPlaceholderText("Total Waktu (menit)")
        layout.addWidget(self.input_waktu)

        self.tombol_proses = QPushButton("Proses Jadwal Optimal", self)
        self.tombol_proses.clicked.connect(self.proses_jadwal)
        layout.addWidget(self.tombol_proses)

        self.table_jadwal = QTableWidget(self)
        self.table_jadwal.setColumnCount(3)
        self.table_jadwal.setHorizontalHeaderLabels(['Nama', 'Durasi', 'Prioritas'])
        layout.addWidget(self.table_jadwal)

        self.label_skor = QLabel("Total Skor: 0", self)
        layout.addWidget(self.label_skor)

        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.handle_timeout)
        self.timeout_duration = 3600000

        self.setLayout(layout)
        self.daftar_aktivitas = []

    def show_error(self, pesan):
        QMessageBox.warning(self, "Input Tidak Valid", pesan)

    def tambah_aktivitas(self):
        nama = self.input_nama.text().strip()
        if not nama:
            self.show_error("Nama aktivitas tidak boleh kosong.")
            return

        try:
            durasi = int(self.input_durasi.text())
            prioritas = int(self.input_prioritas.text())
            if durasi <= 0:
                raise ValueError("Durasi harus lebih dari 0.")
            if not (1 <= prioritas <= 10):
                raise ValueError("Prioritas harus antara 1 dan 10.")
        except ValueError:
            self.show_error("Durasi dan Prioritas harus berupa angka valid (durasi > 0, prioritas 1-10).")
            return

        aktivitas = Aktivitas(nama, durasi, prioritas)
        self.daftar_aktivitas.append(aktivitas)

        row_position = self.table_aktivitas.rowCount()
        self.table_aktivitas.insertRow(row_position)
        self.table_aktivitas.setItem(row_position, 0, QTableWidgetItem(nama))
        self.table_aktivitas.setItem(row_position, 1, QTableWidgetItem(str(durasi)))
        self.table_aktivitas.setItem(row_position, 2, QTableWidgetItem(str(prioritas)))

        self.input_nama.clear()
        self.input_durasi.clear()
        self.input_prioritas.clear()

    def import_dari_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File JSON", "", "JSON Files (*.json)")
        if not file_path:
            return

        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                for item in data:
                    nama = item.get("nama", "").strip()
                    durasi = item.get("durasi")
                    prioritas = item.get("prioritas")

                    if not nama or not isinstance(durasi, int) or not isinstance(prioritas, int):
                        continue
                    if durasi <= 0 or not (1 <= prioritas <= 10):
                        continue

                    aktivitas = Aktivitas(nama, durasi, prioritas)
                    self.daftar_aktivitas.append(aktivitas)

                    row_position = self.table_aktivitas.rowCount()
                    self.table_aktivitas.insertRow(row_position)
                    self.table_aktivitas.setItem(row_position, 0, QTableWidgetItem(nama))
                    self.table_aktivitas.setItem(row_position, 1, QTableWidgetItem(str(durasi)))
                    self.table_aktivitas.setItem(row_position, 2, QTableWidgetItem(str(prioritas)))
        except Exception as e:
            self.show_error(f"Gagal memuat file JSON:\n{e}")

    def proses_jadwal(self):
        try:
            total_waktu = int(self.input_waktu.text())
            if total_waktu <= 0:
                raise ValueError
        except ValueError:
            self.show_error("Total waktu harus angka lebih dari 0.")
            return

        if not self.daftar_aktivitas:
            self.show_error("Tidak ada aktivitas yang ditambahkan.")
            return

        # Nonaktifkan tombol
        self.tombol_proses.setEnabled(False)
        self.label_skor.setText("Memproses...")

        # Jalankan thread
        self.worker = WorkerThread(self.daftar_aktivitas, total_waktu)
        self.worker.hasil_selesai.connect(self.tampilkan_hasil_jadwal)
        self.worker.start()
        
        self.timeout_timer.start(self.timeout_duration)
        
    def tampilkan_hasil_jadwal(self, hasil, elapsed_time_ms):
        self.table_jadwal.setRowCount(0)
        for aktivitas in hasil['jadwal']:
            row_position = self.table_jadwal.rowCount()
            self.table_jadwal.insertRow(row_position)
            self.table_jadwal.setItem(row_position, 0, QTableWidgetItem(aktivitas.nama))
            self.table_jadwal.setItem(row_position, 1, QTableWidgetItem(str(aktivitas.durasi)))
            self.table_jadwal.setItem(row_position, 2, QTableWidgetItem(str(aktivitas.prioritas)))

        self.label_skor.setText(f"Total Skor: {hasil['skor']} | Waktu Eksekusi: {elapsed_time_ms:.2f} ms")
        self.tombol_proses.setEnabled(True)

        self.timeout_timer.stop()  # Hentikan timer jika proses selesai


    def clear_aktivitas(self):
        self.daftar_aktivitas.clear()
        self.table_aktivitas.setRowCount(0)
        self.table_jadwal.setRowCount(0)
        self.label_skor.setText("Total Skor: 0")
        self.input_waktu.clear()

    def handle_timeout(self):
        if self.worker.isRunning():
            self.worker.stop()
            self.label_skor.setText("Gagal: Waktu eksekusi melebihi batas (Timeout)")
            QMessageBox.critical(self, "Timeout", "Proses memerlukan waktu yang terlalu lama sehingga dihentikan")
            self.tombol_proses.setEnabled(True) 

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
