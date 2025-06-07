class Aktivitas:
    def __init__(self, nama, durasi, prioritas):
        self.nama = nama
        self.durasi = durasi
        self.prioritas = prioritas

    def __repr__(self):
        return f"{self.nama} ({self.durasi}m, P{self.prioritas})"

def jadwal_optimal(daftar_aktivitas, total_waktu):
    # Urutkan berdasarkan efisiensi prioritas/durasi
    aktivitas_urut = sorted(
        daftar_aktivitas,
        key=lambda x: x.prioritas / x.durasi,
        reverse=True
    )

    hasil_terbaik = {
        'jadwal': [],
        'skor': 0
    }

    max_skor_teoretis = sum(a.prioritas for a in aktivitas_urut)  
    ambang_kepuasan = int(max_skor_teoretis * 0.80)  

    def backtrack(index, waktu_tersisa, jadwal_sementara, skor_sementara, skor_sisa):
        nonlocal hasil_terbaik

        # Pruning: jika sisa skor maksimal tak akan melampaui skor terbaik → pangkas
        if skor_sementara + skor_sisa <= hasil_terbaik['skor']:
            return

        # Pruning: cukup puas jika sudah mencapai skor 95% dari maksimal
        if hasil_terbaik['skor'] >= ambang_kepuasan:
            return

        if skor_sementara > hasil_terbaik['skor']:
            hasil_terbaik['jadwal'] = jadwal_sementara[:]
            hasil_terbaik['skor'] = skor_sementara

        for i in range(index, len(aktivitas_urut)):
            akt = aktivitas_urut[i]

            if akt.durasi > waktu_tersisa:
                continue

            jadwal_sementara.append(akt)
            backtrack(
                i + 1,
                waktu_tersisa - akt.durasi,
                jadwal_sementara,
                skor_sementara + akt.prioritas,
                skor_sisa - akt.prioritas
            )
            jadwal_sementara.pop()

    total_prioritas = sum(a.prioritas for a in aktivitas_urut)
    backtrack(0, total_waktu, [], 0, total_prioritas)

    return hasil_terbaik
