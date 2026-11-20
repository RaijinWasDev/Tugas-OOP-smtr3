# Minggu 9 — Nilai mahasiswa

Untuk presentasi, daftarkan mahasiswa contoh, setujui KRS, lalu isi dosen pengampu di menu Jadwal. Buka Nilai, pilih mata kuliah dan masukkan nama dosen sesuai jadwal. Simpan B, lalu koreksi menjadi A dengan alasan. Tunjukkan perubahan IPS/IPK serta nama dosen, waktu UTC, nilai lama, nilai baru dan alasan di riwayat.

## Keputusan rancangan (ADR)

Nilai tersimpan pada detail KRS. Huruf mengacu ke skala nilai. Bobot lama tetap terisi untuk kompatibilitas prasyarat KRS. Perubahan nilai dan riwayat ditulis dalam satu transaksi. IPS memakai seluruh mata kuliah yang sudah dinilai pada semester pilihan. IPK mengambil nilai lulus terbaik per kode mata kuliah hingga semester pilihan. Keduanya dibobot SKS dan dibulatkan sekali dengan Decimal dan ROUND_HALF_UP.

## Pertanyaan untuk dosen

Apakah D (1,00) dianggap lulus untuk IPK, atau batasnya C (2,00)? Sementara A, B, C dihitung dalam IPK. Aturan ini diatur lewat kolom lulus di skala_nilai. Contoh dua mata kuliah masing-masing 3 SKS dengan nilai A dan D menghasilkan IPS 2,50 dan IPK 4,00.

## Jurnal penggunaan AI dan batas demo

AI membantu menyusun migrasi, formulir, kalkulator dan pengujian. Pemeriksaan mencakup pengulangan mata kuliah, semester kosong dan pembulatan 3,125 menjadi 3,13. Presensi masih simulasi: ST101 sebesar 70%, mata kuliah lain 100%. Nilai membutuhkan minimal 75%. Admin memperagakan peran dosen dengan mengisi nama pengampu. Sistem produksi memerlukan identitas dosen dari sesi login dan data presensi aktual. Gunakan data mahasiswa fiktif.

Materi: https://youtu.be/lYj5oyiclPU
