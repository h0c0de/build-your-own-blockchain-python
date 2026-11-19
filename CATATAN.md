# Catatan — Blockchain (van Flymen)

Satu halaman per irisan: konsep inti dan temuan selama membangun.
Panduan: Daniel van Flymen, "Learn Blockchains by Building One".

## Irisan 1 — Kelas inti

Konsep inti: **rantai = daftar blok yang masing-masing membawa
hash blok sebelumnya.** Ubah satu isi lama, dan hash-nya berubah,
sehingga blok sesudahnya menunjuk hash yang salah — kerusakan
terdeteksi tanpa perlu salinan pembanding. Blok adalah dict:
index, timestamp, transactions, proof, previous_hash. Blok
pertama (genesis) disepakati konstan: proof 100, previous_hash 1.

Hash blok = SHA-256 atas JSON dengan kunci terurut
(`sort_keys=True`) — tanpa itu, dict yang sama bisa ber-hash
beda hanya karena urutan penulisan kunci.

Proof of Work di sini sengaja primitif: cari p' terkecil agar
SHA-256 dari gabungan teks f'{proof_lama}{p'}' berawalan
"0000". Mencarinya mahal (puluhan ribu tebakan), memeriksa
satu tebakan sekejap — asimetri itulah inti PoW.

Temuan:
- **Jangkar artikel lolos persis**: proof_of_work(100) → 35293
  dan proof_of_work(35293) → 35089, sama dengan proof blok 2
  dan 3 pada contoh rantai yang diterbitkan van Flymen. Karena
  PoW hanya bergantung pada proof sebelumnya (timestamp tidak
  ikut), contoh cetak artikel berfungsi sebagai uji
  known-answer yang sempurna.
- Contoh mainan pembuka artikel (x=5, hash harus berakhiran 0)
  juga reproduksi persis: y=21, hash penuh
  1253e9373e...5e860 cocok dengan yang dicetak.
- Dua penambangan penuh hanya ±0,15 detik di VM ini — empat
  nol masih ringan; artikelnya sendiri memperingatkan satu nol
  tambahan mengubah waktu secara drastis (faktor ±16 per nol).
- previous_hash genesis berupa **int** 1, bukan string —
  ketidakkonsistenan tipe yang disengaja panduan dan kami
  pertahankan apa adanya.

## Irisan 2 — API node

Konsep inti: **satu proses server = satu node.** Kelas rantai
dibungkus Flask menjadi tiga endpoint: `POST /transactions/new`
mengantrekan transaksi (201, atau 400 "Missing values" bila
kolom kurang), `GET /mine` menjalankan PoW lalu menambahkan
transaksi imbalan (pengirim "0", 1 koin, ke alamat node
sendiri) sebelum menempa blok, dan `GET /chain` membuang isi
rantai + panjangnya. Alamat node = uuid4 tanpa tanda hubung.

Temuan:
- **Alur artikel bereproduksi utuh lewat HTTP**: transaksi
  contoh cURL artikel → mine → mine → rantai 3 blok dengan
  proof 100 → 35293 → 35089, persis contoh tercetaknya —
  kini lewat tumpukan Flask sungguhan, bukan hanya kelas.
- Urutan transaksi dalam blok hasil tambang: transaksi pemakai
  yang mengantre lebih dulu, imbalan penambang **terakhir** —
  karena /mine menambahkan imbalan sesudah PoW, sebelum
  new_block membekukan antrean.
- Flask modern (3.1.3) menjalankan kode pola 0.12.2 tanpa satu
  pun penyesuaian API — jsonify/request/route tidak berubah
  dalam 8 tahun untuk permukaan yang dipakai panduan.
- Uji memakai test_client Flask dan mengganti rantai global
  modul dengan instance baru — fungsi view membaca global
  `blockchain` saat dipanggil, jadi penggantian ini bersih
  tanpa mengubah kode panduan.

## Irisan 3 — Jaringan & konsensus

Konsep inti: **konsensus = rantai sah terpanjang menang.**
`register_node` menyimpan netloc tetangga dalam set (idempoten).
`valid_chain` menelusuri rantai dan memeriksa dua hal per blok:
previous_hash harus sama dengan hash blok sebelumnya, dan
pasangan proof harus lolos valid_proof. `resolve_conflicts`
mengunduh /chain dari semua tetangga dan mengganti rantai
sendiri hanya bila ditemukan rantai yang lebih panjang DAN sah.

Temuan:
- **Celah ujung yang jujur**: valid_chain memeriksa tunjukan &
  proof tiap blok, tetapi tidak pernah meng-hash isi blok
  terakhir itu sendiri. Mengubah amount di blok **ujung**
  masih lolos validasi — dan baru tertangkap sesudah blok
  berikutnya lahir menunjuk hash aslinya. Mengubah blok tengah
  atau proof langsung gugur. Ini sifat asli algoritma panduan:
  integritas blok selalu dijamin oleh penerusnya, dan ujung
  rantai adalah titik terlemahnya — alasan dunia nyata memakai
  kedalaman konfirmasi.
- Konsensus dua server hidup berjalan persis seperti demo
  artikel: node A (1 blok) mendaftar ke B (3 blok), resolve →
  "Our chain was replaced", dan /chain A menjadi byte-identik
  dengan B. Resolve kedua: "authoritative". Rantai sama
  panjang tidak pernah menggantikan.
- register tanpa daftar nodes → 400 dengan pesan artikel apa
  adanya.

## Irisan 4 — Baterai akhir & terbit

Konsep inti: **fork adalah hal biasa; konsensuslah yang
memilih sejarah mana yang kanonik.** Skenario finale
mempertemukan dua rantai yang tumbuh sendiri-sendiri: node C
menambang blok berisi transaksi pemakai, node D menambang
lebih panjang sendirian. Saat C resolve, rantainya diganti
rantai D — dan transaksi pemakai C menjadi **yatim**: hilang
dari sejarah kanonik tanpa jejak, karena panduan tidak punya
mempool penyelamat. Lalu C menambang di atas rantai adopsi
hingga lebih panjang, dan D ganti mengadopsinya: lingkaran
konsensus penuh, kedua rantai berakhir identik dan sah.

Temuan:
- Regresi penuh 26 + 22 + 19 hijau, finale 13 hijau — total
  80 pemeriksaan untuk satu berkas ±330 baris.
- Transaksi yatim adalah pelajaran termahal blockchain ini:
  "sudah masuk blok" tidak berarti "final". Di Bitcoin pun
  transaksi di cabang kalah kembali ke mempool; di panduan
  ini ia lenyap — batas yang dicatat terbuka.
- Seluruh janji panduan terpenuhi apa adanya: satu berkas,
  tiga lapis (rantai → API → konsensus), dan contoh cetak
  artikelnya berfungsi sebagai wasit di dua irisan berbeda.
