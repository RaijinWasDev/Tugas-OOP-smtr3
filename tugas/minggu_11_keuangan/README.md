# Minggu 11 — Keuangan SPP

Di tab **Keuangan**, pilih awal semester dan buat tagihan. Gunakan mahasiswa fiktif yang pendaftarannya sudah disetujui. Coba bayar sebagian, lalu lunasi sisanya. Untuk mencoba blokir KRS, buat tagihan dengan awal semester lebih dari 14 hari yang lalu. Setelah tunggakan lunas, coba tambah mata kuliah kembali.

## Asumsi demo

Semester mulai 1 Februari dan 1 Agustus. Selama server hidup, pekerjaan latar memeriksa semester saat startup lalu setiap lima menit. Tagihan unik per mahasiswa dan awal semester. Jatuh tempo 14 hari setelah awal semester. Fakultas Teknik Rp5 juta dan Ekonomi Rp4 juta. Denda contoh sebesar 1% dari pokok, sekali, jika masih ada saldo saat jatuh tempo. Jika pembayaran melebihi sisa, seluruh penerimaan dicatat dan saldo tagihan menjadi nol. Tunggakan memblokir tambah mata kuliah dan pengajuan KRS. Pengingat dibuat sekali per minggu per tagihan tertunggak.

Dashboard memakai data transaksi lokal. Persentase per prodi membandingkan uang yang diterapkan pada tagihan dengan total kewajiban. Persentase mahasiswa lunas memakai jumlah mahasiswa tertagih sebagai penyebut. Pendapatan bulanan menghitung seluruh pembayaran. Rekomendasi dan sepuluh tunggakan terbesar dihitung dari data yang sama; laporan JSON tersedia di GET /api/spp/dashboard.

## Simulasi gateway

Sebelum membuka launcher, tetapkan SPP_WEBHOOK_SECRET di terminal. Gunakan nilai rahasia khusus demo. Contoh berikut dijalankan dari PowerShell, dengan secret yang sama dan ID tagihan yang masih memiliki saldo:

~~~powershell
$body = '{"transaction_id":"demo-001","billing_id":1,"amount":100000,"status":"success"}'
[IO.File]::WriteAllText("$PWD/payload.tmp", $body, [Text.UTF8Encoding]::new($false))
$hmac = [Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($env:SPP_WEBHOOK_SECRET))
$sig = [BitConverter]::ToString($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($body))).Replace('-','').ToLowerInvariant()
curl.exe -H "Content-Type: application/json" -H "X-Signature: $sig" --data-binary "@payload.tmp" http://127.0.0.1:8007/api/spp/webhook
~~~

ID transaksi yang sama dengan data pembayaran yang sama aman dikirim kembali. Bukti pembayaran dan pengingat masuk ke antrean email. Untuk pengiriman sungguhan, atur SPP_SMTP_HOST, SPP_SMTP_PORT (default 587), SPP_SMTP_FROM serta SPP_SMTP_USER dan SPP_SMTP_PASSWORD bila server meminta login. Pengiriman memakai STARTTLS. Tanpa SMTP, pesan tersimpan untuk dikirim setelah konfigurasi tersedia.
Untuk laporan dari CSV, POST isi CSV UTF-8 ke /api/spp/laporan-csv dengan header X-Admin-Key. Kolom nim,jumlah,tanggal,status berisi satu baris per penerimaan, tanggal ISO dan jumlah rupiah. Pendapatan dihitung dari CSV. Saldo, tingkat pelunasan dan umur tunggakan memerlukan buku tagihan di database karena CSV pembayaran tidak memuat kewajiban atau tanggal jatuh tempo.
