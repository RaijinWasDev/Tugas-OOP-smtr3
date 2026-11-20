# Sevima Mini · Minggu 2
Baca [class diagram](../perancangan/diagrams/class-diagram.mmd), [use case](../perancangan/diagrams/use-case.puml), [sequence PMB](../perancangan/diagrams/sequence-pmb.mmd), dan [sequence KRS](../perancangan/diagrams/sequence-krs.mmd). Acuan: [video minggu 2](https://www.youtube.com/watch?v=dS1aqiUpoFk&t=1596s).

Sistem PMB pada use case adalah portal eksternal yang meneruskan pendaftaran. PMBService adalah layanan internal yang memprosesnya. Dosen PA meninjau KRS dan dosen pengampu memasukkan nilai. Satu orang bisa memegang kedua peran.

Untuk demo, ikuti satu pendaftar dari status pending sampai menerima NIM. Kemudian coba KRS 26 SKS dengan dua jadwal bertumpuk. Mahasiswa menerima kedua alasan dan dapat memperbaiki pilihan. Ulangi dengan 24 SKS tanpa kesalahan lain. Status berubah menjadi SUBMITTED dan dosen PA menerima pemberitahuan.

Saat merekam, tampilkan prompt dan hasilnya, jelaskan satu perubahan manual, lalu tunjukkan diagram sebelum dan sesudah. Simpan tangkapan layar dari proses nyata dan lengkapi [log](../perancangan/prompts/ai-usage.md).
