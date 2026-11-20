# Sevima Mini

## Progres mingguan

- [Minggu 1 â€” Rancangan awal](progres/minggu-01.md)
- [Minggu 2 â€” Diagram UML](progres/minggu-02.md)
- [Minggu 3 â€” Pendaftaran PMB](progres/minggu-03.md)
- [Minggu 4 â€” Persetujuan PMB](progres/minggu-04.md)
- [Minggu 5 â€” Pengisian KRS](progres/minggu-05.md)
- [Minggu 6 â€” Persetujuan KRS](progres/minggu-06.md)
- [Minggu 7 â€” Jadwal dan portal admin](progres/minggu-07.md)

[Laporan final UML](perancangan/docs/Final-UML.pdf)

## Demo UTS

Jalankan Buka-Sevima.cmd dari folder proyek, lalu buka http://127.0.0.1:8007/admin. Ikuti alur Pendaftaran, KRS, lalu Jadwal. Tag minggu-01 hingga minggu-07 menandai versi tiap tahap. Tag uts menandai versi presentasi. Riwayat ini disusun dari arsip mingguan.

## Koreksi setelah persetujuan
Admin bersama dosen PA dapat membuka kembali KRS melalui POST /api/krs/{nim}/{semester}/reopen dengan versi terbaru dan alasan. Setelah status menjadi revision, tambah atau hapus mata kuliah, lalu ajukan dan setujui kembali. Total SKS mengikuti pilihan mata kuliah.
