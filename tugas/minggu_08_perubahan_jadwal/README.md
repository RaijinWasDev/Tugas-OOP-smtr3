# Minggu 8 - Perubahan jadwal dan ruangan

Pada branch tugas/minggu-08, jalankan Buka-Sevima.cmd dari folder utama agar migrasi 005 menyiapkan log notifikasi. Login dan buka menu Jadwal.

1. Simpan Algoritma pada Senin 08.00-10.00 di A101 dengan dosen D01.
2. Daftarkan mahasiswa contoh, tambahkan Algoritma ke KRS, ajukan dan setujui.
3. Coba jadwalkan Basis Data dengan hari, jam, ruang dan dosen yang sama. Klik Pilih pada salah satu alternatif, lalu Simpan jadwal.
4. Ubah ruangan Algoritma menjadi B202. Buka Riwayat notifikasi jadwal untuk melihat simulasi email mahasiswa, SMS dosen, dan push admin. Di menu KRS, mahasiswa yang mengambil Algoritma perlu meninjau kembali KRS.
5. Menyimpan jadwal yang identik tidak mengirim notifikasi baru. Menghapus jadwal juga memberi tahu pihak terdampak.

Pencarian alternatif menggunakan batasan kapasitas, ketersediaan dosen dan ruangan. Pohon interval memeriksa bentrok per hari. Algoritme heuristik lokal mengurutkan pilihan menurut kedekatan hari, jam dan ruangan awal, lalu menawarkan hingga tiga opsi. Simulasi bekerja offline tanpa layanan AI eksternal.

~~~mermaid
sequenceDiagram
    actor Admin
    participant Portal
    participant Manager as NotificationManager
    participant Observer
    participant DB
    Admin->>Portal: Ubah jadwal
    Portal->>DB: Simpan jadwal dan tandai KRS terdampak
    Portal->>Manager: Umumkan perubahan
    loop Mahasiswa, dosen, admin
        Manager->>Observer: Kirim peristiwa
        Observer->>DB: Catat penerima, media dan pesan
    end
    Portal->>DB: Commit transaksi
    Portal-->>Admin: Tampilkan hasil dan log
~~~

[Video pembelajaran minggu 8](https://youtu.be/HpGKeEh--Co)
