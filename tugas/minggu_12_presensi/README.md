# Minggu 12 — Presensi QR

1. Di halaman admin, setujui KRS mahasiswa contoh. Di tab Jadwal, pastikan hari, waktu WIB dan dosen pengampu sesuai. Untuk demo langsung, gunakan hari ini dan jam mulai beberapa menit sebelum waktu demo.
2. Di tab Presensi, pilih mata kuliah dan semester, masukkan dosen pengampu, lalu tampilkan QR. Kamera ponsel dapat membaca tautannya. Untuk presentasi di satu laptop gunakan **Buka halaman scan di laptop ini**. Isi NIM dan kirim.
3. Tunjukkan penolakan untuk NIM di luar kelas atau pemindaian kedua. QR berlaku maksimal 15 menit dan bisa diterbitkan ulang dalam 30 menit pertama kelas. QR lama langsung kedaluwarsa. Mulai menit ke-15, mahasiswa yang berhasil memindai dicatat terlambat.
4. Setelah jendela presensi ditutup, klik **Muat ulang**. Hadir dan terlambat sama-sama dihitung hadir. Penyebut adalah jumlah sesi tertutup yang mencantumkan mahasiswa sebagai peserta. Sesi menyimpan daftar peserta dari KRS disetujui ketika pertama dibuka. Modul Nilai memakai hasil ini dengan batas 75%; sebelum ada sesi selesai, presensi belum mencukupi.
5. Klik **Unduh Excel**. Laporan JSON di GET /attendance/report juga memuat mahasiswa di bawah 75%, saran konseling jika absen berulang pada slot yang sama, dan saran evaluasi jadwal jika sedikitnya 40% peserta absen. Analisis berbasis aturan dapat berjalan offline.

## Akses demo

Launcher biasa memakai alamat laptop sendiri. Untuk ponsel di Wi-Fi yang sama, jalankan server pada alamat LAN laptop di terminal dengan kunci admin yang sudah disetel, lalu buka halaman admin lewat alamat LAN tersebut sebelum menampilkan QR. Contoh perintah untuk laptop dengan IP 192.168.1.20:

~~~powershell
python -m alembic upgrade head
$env:PMB_ADMIN_KEY = [guid]::NewGuid().ToString()
Write-Host $env:PMB_ADMIN_KEY
python -m uvicorn main:app --host 192.168.1.20 --port 8007
~~~

Gunakan http://192.168.1.20:8007/admin dan sesuaikan alamat dengan laptop. Kunci admin hanya digunakan di portal dosen. Halaman mahasiswa memakai QR dan NIM untuk simulasi; identitas mahasiswa belum terhubung ke login kampus. Batas 30 percobaan per menit per alamat IP. Geolokasi bersifat opsional dan tidak digunakan. Hasil Excel dan endpoint laporan hanya tersedia dari sesi admin.
