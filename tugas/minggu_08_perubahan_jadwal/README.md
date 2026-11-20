# Minggu 8 - Perubahan jadwal dan ruangan

## Demo

Dari branch tugas/minggu-08, jalankan Buka-Sevima.cmd. Migrasi menyiapkan antrean outbox. Masuk sebagai admin dan ikuti langkah berikut.

1. Simpan Algoritma pada Senin 08.00-10.00 di A101 dengan dosen D01. Buat mahasiswa demo dan setujui KRS yang berisi Algoritma.
2. Coba simpan Basis Data pada jam, ruang, dan dosen yang sama. Portal menunjukkan bentrok. Pilih saran lalu simpan. Server memeriksa lagi ketersediaan pada saat penyimpanan.
3. Pindahkan ruang Algoritma. Tunjukkan riwayat Email mahasiswa, SMS dosen, dan Push admin. KRS berstatus submitted atau approved yang memuat Algoritma kembali ke revision. Riwayat KRS mencatat aktor sistem.
4. Di Ekspor kalender semester, pilih tanggal awal dan akhir lalu unduh jadwal. Kalender menggunakan jam kampus WIB, perulangan mingguan, UID stabil per mata kuliah dan awal semester, serta SEQUENCE yang bertambah saat ada perubahan.

## Menjalankan rekomendasi AI

Dengan Ollama aktif di localhost:11434 dan model yang sudah terpasang, jalankan dari PowerShell yang sama:

~~~powershell
$env:SEVIMA_MODEL = "qwen2.5:3b"
.\Buka-Sevima.cmd
~~~

Ganti nama model sesuai instalasi. Portal menandai sumber rekomendasi. Tanpa model atau ketika layanan tidak tersedia, demo memakai aturan lokal. Model menerima slot yang dihitung server dan hanya memilih serta memberi alasan. Server menyaring hari, waktu, ruang, duplikasi, dan kapasitas melalui pencocokan dengan katalog slot valid. Pengujian menggunakan penyedia AI tiruan.

## Sequence diagram

~~~mermaid
sequenceDiagram
    actor Admin
    participant Jadwal
    participant DB
    participant Dispatcher
    participant Observer
    Admin->>Jadwal: Simpan perubahan
    Jadwal->>DB: Ubah jadwal, revisi KRS, simpan event pending
    Jadwal->>DB: Commit
    Jadwal->>Dispatcher: Proses event setelah commit
    loop Mahasiswa, dosen, admin
        Dispatcher->>Observer: Teruskan event ke subscriber
        Observer->>DB: Catat kanal dan penerima sekali per event
    end
    Dispatcher->>DB: Tandai sent atau simpan kegagalan untuk retry
~~~

Jika proses berhenti sesudah commit, event tetap pending. Pada riwayat notifikasi, klik Kirim ulang notifikasi tertunda. Pengiriman merupakan simulasi melalui log database. Tiap observer mempunyai savepoint tersendiri. Kunci unik event, kanal, dan penerima mencegah duplikasi saat dicoba kembali.

## Catatan penggunaan AI dan OPAR

- Observe: implementasi awal menulis log sebelum commit dan belum menyediakan ekspor kalender.
- Plan: simpan event bersama perubahan jadwal, pisahkan dispatcher, serta batasi pilihan model ke slot valid.
- Act: Codex membantu mengubah layanan, migrasi, portal, diagram dan tes berdasarkan PDF serta transkrip minggu 8.
- Reflect: tes mensimulasikan rollback, observer gagal, retry dan keluaran AI yang salah. Saat presentasi, jelaskan mengapa rollback harus membatalkan event dan mengapa ketersediaan diperiksa lagi sebelum menyimpan pilihan admin.

[Video pembelajaran minggu 8](https://youtu.be/HpGKeEh--Co)
