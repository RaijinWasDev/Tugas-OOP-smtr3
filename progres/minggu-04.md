# PMB minggu 4
Mulai dari terminal PowerShell pada folder minggu-04. Gunakan instalasi Python 3.11 yang memiliki paket berikut.

~~~powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
$env:PMB_ADMIN_KEY = [guid]::NewGuid().ToString()
$env:PMB_ADMIN_KEY | Set-Clipboard
python -m uvicorn main:app --port 8004
~~~

## Demo di Swagger
1. Buka http://127.0.0.1:8004/docs. Pilih POST /api/pmb/register, klik Try it out, tempel isi contoh.json lalu Execute. Salin id dari respons 201.
2. GET /api/pmb/status/{id} menampilkan pending dan nim kosong.
3. Klik Authorize dan tempel kunci demo dari clipboard. PUT /api/pmb/approve/{id} mengubah status menjadi approved. Ulangi dengan ID sama dan bandingkan NIM.
4. Daftar memakai email fiktif lain dan setujui. Untuk prodi dan tahun yang sama, empat digit terakhir naik satu. GET /api/pmb/stats menampilkan jumlah per status dan prodi.
5. Uji pula email ganda (409), format HP salah (400), dan ID yang tidak ditemukan (404). Sembunyikan kunci admin saat merekam.
 
## Mengapa NIM tetap unik
Format contoh 2026001-0001 menggabungkan tahun persetujuan, kode prodi 001 dan urutan empat digit. SQLite mengunci transaksi tulis dengan BEGIN IMMEDIATE sebelum membaca pendaftar dan nomor terakhir. Permintaan kedua menunggu transaksi pertama selesai. Jika ID sama, ia membaca NIM yang sudah tersimpan. Jika ID berbeda, ia membaca nomor terakhir yang baru. Jika transaksi gagal, status dan NIM dibatalkan bersama. Indeks unik pada nim memberi perlindungan tambahan.

## Bukti dan batas pengujian
Jalankan python -m pytest -q --cov --cov-report=term-missing --cov-report=html:coverage-html. Sembilan kasus lulus, cakupan baris aplikasi 93,12% (176 dari 189). Tes memanggil fungsi router, service, validasi, dan SQL nyata, termasuk dua sesi bersamaan, serta memeriksa kontrak OpenAPI. Tes tidak menjalankan browser. Migrasi Alembic telah dijalankan naik, turun, lalu naik pada database demo kosong. Jangan menjalankan downgrade base pada database berisi data yang ingin disimpan.

## Log AI minggu 4
Permintaan Panji adalah melanjutkan video PBO minggu keempat. Codex membaca PDF tugas, mengembangkan salinan proyek minggu ketiga, menulis fungsi persetujuan dan statistik, serta menjalankan migrasi dan tes. Pilihan desain untuk demo ini adalah SQLite dengan kunci tulis dan kunci admin melalui header X-Admin-Key. Catat hasil percobaan pribadi, perubahan manual, serta tautan commit saat merekam.

Acuan: https://youtu.be/mbDqnE8VO1s dan modul tertulis implementasi PMB minggu 3-4. Transkrip video keempat tidak tersedia ketika diperiksa.
