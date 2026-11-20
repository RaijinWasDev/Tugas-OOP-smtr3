# PMB minggu 3
Buka terminal di folder minggu-03. Perintah berikut untuk PowerShell di laptop Panji.
```powershell
python -m pip install -r requirements.txt
python init_demo.py
python -m uvicorn main:app --port 8003
```
Buka http://127.0.0.1:8003/docs dan coba POST /api/pmb/register memakai contoh.json. ID prodi 1 adalah Teknik Informatika; jalur 1, 2, 3 masing-masing SNBP, SNBT dan Mandiri. Setelah berhasil, kirim ulang email yang sama. Coba juga nomor telepon rumah dan ID prodi 99 dengan email baru.

## Migrasi dan bukti
Untuk instalasi baru, pasang requirements.txt dan jalankan python -m alembic upgrade head dari folder ini. Revisi 001 membuat tiga tabel dan data referensi. Pada salinan database latihan kosongkan kembali dengan python -m alembic downgrade base lalu ulangi upgrade. Downgrade menghapus tabel dan isi PMB. cek_demo.py menguji SQL dua arah dan jalur registrasi pada database sementara. init_demo.py menyiapkan database demo memakai revisi SQL yang sama jika Alembic belum tersedia.

## Keputusan validasi
Nomor 08, 628 dan +628 yang valid disimpan dalam satu format lokal. Status validasi input memakai 400 sesuai contoh tes modul. Email duplikat menghasilkan 409 dan pendaftaran berhasil menghasilkan 201. NIM masih kosong saat pending.

## Log penggunaan AI
Minggu 3, fitur pendaftaran. Panji meminta Codex melanjutkan proyek berdasarkan video ketiga dan file tugas. Hasil bantuan berupa model SQLAlchemy, migrasi, skema Pydantic, service, router dan uji contoh. Catat perubahan manual, tangkapan layar Swagger dan tautan commit setelah dikerjakan saat demo. Tandai commit yang dibantu AI.
