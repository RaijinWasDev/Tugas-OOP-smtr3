# Sevima Mini · Minggu 1
Draf berbantuan AI untuk ditinjau Panji berdasarkan video PBO minggu 01.

## Membaca diagram
Saat calon mahasiswa diterima, sistem membuat data Mahasiswa dengan NIM dan mengaitkannya ke pendaftaran asal. Setiap mahasiswa memiliki paling banyak satu KRS untuk satu periode. Satu baris Enrollment menyatakan satu mata kuliah dan jadwal yang dipilih dalam KRS tersebut. Jadwal pilihan harus milik mata kuliah yang sama. Nilai baru muncul setelah dosen menilai pengambilan itu.

## Keputusan untuk dibahas saat rekaman
Grade melekat pada Enrollment. Jika mahasiswa mengulang mata kuliah tahun depan, nilai lama dan nilai baru dapat ditelusuri ke periode masing-masing. Konsekuensinya, sistem perlu membaca riwayat pengambilan mata kuliah saat membuat transkrip.

Status persetujuan disimpan pada KRS. Baris Enrollment membaca status dari KRS induknya agar baris dalam satu pengajuan mengikuti keputusan yang sama.

## Pemeriksaan mandiri
Coba telusuri bagaimana satu mahasiswa bisa mengambil dua mata kuliah dan memperoleh nilai berbeda. Periksa relasi di diagram lalu catat revisi yang benar-benar kamu lakukan. Draf awal ini belum memuat hasil revisi manual atau rekaman presentasi.
