# Rencana — Build Ketiga Belas: Blockchain (van Flymen)

Mengikuti panduan **Daniel van Flymen**, *"Learn Blockchains by
Building One"* (HackerNoon, 2017) — entri Python kategori
Blockchain / Cryptocurrency di repo
codecrafters-io/build-your-own-x.

Panduan: https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
Kode akhir penulis: https://github.com/dvf/blockchain

## Isi panduan (terverifikasi 19 Nov 2026, dibaca utuh)

Satu berkas `blockchain.py`, empat langkah: (1) kelas
`Blockchain` — blok {index, timestamp, transactions, proof,
previous_hash}, blok genesis (proof 100, previous_hash 1),
hash SHA-256 atas JSON terurut, Proof of Work "hash gabungan
proof lama+baru berawalan 0000"; (2) API Flask — `GET /mine`,
`POST /transactions/new`, `GET /chain`, imbalan penambang
1 koin dari pengirim "0"; (3) interaksi via HTTP; (4) konsensus
— `register_node`, `valid_chain`, `resolve_conflicts` (rantai
sah terpanjang menang), `POST /nodes/register`,
`GET /nodes/resolve`.

Jangkar deterministik dari contoh rantai yang diterbitkan
artikelnya, SUDAH diverifikasi komputasi 19 Nov 2026:
proof_of_work(100) = **35293** dan proof_of_work(35293) =
**35089** — persis proof blok 2 dan 3 pada contoh artikel.
Contoh mainan artikel (x=5 → y=21, hash berakhiran 0) juga
cocok: sha256("105") = 1253e9373e...5e860.

## Adaptasi yang dicatat terbuka

- Panduan mematok Flask==0.12.2 (2017, tidak jalan di Python
  3.12). Kami memakai Flask 3.1.3 modern, dipasang lokal di
  `aset/lib` (gitignore) — permukaan API yang dipakai panduan
  (Flask/jsonify/request) tidak berubah.
- `valid_chain` di artikel mencetak debug tiap blok; cetakan
  itu kami hilangkan (kosmetik, dicatat).
- Uji konsensus menjalankan dua server sungguhan pada port
  lokal lewat subprocess — demo finale artikel, diotomatiskan.

## Irisan

- [x] Irisan 1 — Kelas inti: genesis, new_block,
      new_transaction, hash, last_block, proof_of_work,
      valid_proof. Bukti: genesis persis (index 1, proof 100,
      previous_hash 1); proof_of_work(100) → 35293 dan
      (35293) → 35089 persis artikel; hash stabil terhadap
      urutan kunci; contoh mainan y=21.
- [x] Irisan 2 — API node: /mine, /transactions/new, /chain
      lewat Flask test_client. Bukti: alur artikel — transaksi
      201 "Block 2", kolom hilang 400, /mine mengarang blok
      berisi imbalan (sender "0", amount 1), dua kali mine →
      length 3 dengan proof 35293 & 35089.
- [x] Irisan 3 — Jaringan & konsensus: register_node,
      valid_chain, resolve_conflicts + kedua endpoint.
      Bukti: rantai sendiri sah; rantai yang diubah isinya
      (tamper) gugur di valid_chain; dua server hidup — node
      pendek memanggil resolve → rantainya diganti rantai
      node yang lebih panjang, byte-identik.
- [x] Irisan 4 — Baterai akhir & terbit: skenario ujung-ke-
      ujung dua node via HTTP sungguhan, regresi 1–3,
      terbit ke `build-your-own-blockchain-python`.

## Pagar selesai

- [x] Proof artikel (35293, 35089) direproduksi persis oleh
      proof_of_work kami.
- [x] Tamper-evidence terbukti: satu angka diubah → rantai
      ditolak valid_chain.
- [x] Konsensus terbukti antar dua proses server hidup, bukan
      mock.
- [x] `CATATAN.md` satu halaman per irisan: konsep inti + temuan.
- [x] Repo GitHub publik `build-your-own-blockchain-python`
      terbit & terverifikasi.
