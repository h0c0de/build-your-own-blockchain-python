# Build Your Own Blockchain (Python)

Satu blockchain mini utuh dalam satu berkas — blok berantai
hash, Proof of Work, node HTTP, dan konsensus banyak node —
dibangun lapis demi lapis mengikuti panduan **Daniel van
Flymen**:

*[Learn Blockchains by Building One](https://hackernoon.com/learn-blockchains-by-building-one-117428612f46)*
(HackerNoon, 2017)

Bagian dari seri belajar
[build-your-own-x](https://github.com/codecrafters-io/build-your-own-x)
(kategori Blockchain / Cryptocurrency). Ditulis ulang dari nol
sebagai latihan dengan atribusi; bukan salinan berkas asli
penulis.

## Isi

| Berkas | Isi |
| --- | --- |
| `blockchain.py` | **Semuanya dalam satu berkas**, seperti panduan: kelas `Blockchain` (genesis, hash SHA-256 atas JSON terurut, PoW awalan "0000", transaksi), API Flask (`/mine`, `/transactions/new`, `/chain`), dan konsensus (`/nodes/register`, `/nodes/resolve`, rantai sah terpanjang menang). |

## Menjalankan

Butuh Flask & requests (panduan mematok versi 2017; versi
modern berjalan sama):

```
pip install flask requests
python3 blockchain.py -p 5000     # node pertama
python3 blockchain.py -p 5001     # node kedua, terminal lain
```

```
curl http://localhost:5000/mine
curl -X POST -H "Content-Type: application/json" -d \
  '{"sender": "alamatku", "recipient": "alamat-lain", "amount": 5}' \
  http://localhost:5000/transactions/new
curl -X POST -H "Content-Type: application/json" -d \
  '{"nodes": ["http://localhost:5001"]}' \
  http://localhost:5000/nodes/register
curl http://localhost:5000/nodes/resolve
curl http://localhost:5000/chain
```

## Uji

Setiap irisan punya berkas ujinya; finale menjalankan regresi
penuh plus skenario dua node hidup:

```
python3 uji_irisan1.py   # 26 uji — kelas inti, jangkar proof artikel
python3 uji_irisan2.py   # 22 uji — API node (test_client)
python3 uji_irisan3.py   # 19 uji — valid_chain, perusakan, konsensus hidup
python3 uji_irisan4.py   # 13 uji — regresi 1-3 + fork & lingkaran konsensus
```

Sorotan bukti: **proof_of_work(100) menghasilkan 35293 dan
proof_of_work(35293) menghasilkan 35089 — persis proof blok 2
dan 3 pada contoh rantai yang diterbitkan artikelnya** (PoW
hanya bergantung pada proof sebelumnya, jadi contoh cetak itu
uji known-answer yang sempurna). Konsensus diuji antar proses
server sungguhan, bukan mock: rantai yang kalah fork diganti
byte-identik, dan transaksi di cabang yang kalah menjadi yatim.

## Temuan yang dicatat jujur

- `valid_chain` panduan memeriksa tunjukan `previous_hash` dan
  pasangan proof tiap blok, tetapi tidak meng-hash isi blok
  **terakhir** — mengubah isi blok ujung lolos validasi sampai
  ada blok berikutnya yang menunjuk hash aslinya. Integritas
  blok dijamin penerusnya; ujung rantai adalah titik terlemah
  (alasan dunia nyata memakai kedalaman konfirmasi).
- Transaksi pada cabang yang kalah konsensus hilang begitu
  saja — panduan tidak punya mekanisme mempool untuk
  menyelamatkannya.

## Adaptasi yang dicatat terbuka

- **Flask modern** (3.1.3) menggantikan patokan Flask==0.12.2
  (2017, tidak berjalan di Python 3.12); permukaan API yang
  dipakai panduan tidak berubah. Di repo ini Flask dipasang
  lokal di `aset/lib` (gitignore) — sesuaikan `PYTHONPATH`
  atau pasang global.
- Cetakan debug di dalam `valid_chain` artikel dihilangkan.
- Port server dipilih lewat `-p/--port` (dari kode akhir
  penulis sendiri).

Perjalanan irisan demi irisan, konsep inti, dan semua temuan
ada di `CATATAN.md`; peta & pagar selesai di `RENCANA.md`.
