# Uji irisan 1 — kelas Blockchain inti.
# Jangkar terpenting: proof pada contoh rantai yang diterbitkan
# artikel van Flymen — blok 2 proof 35293, blok 3 proof 35089.
import hashlib

from blockchain import Blockchain

lulus = 0


def cek(nama, kondisi):
    global lulus
    assert kondisi, f"GAGAL: {nama}"
    lulus += 1
    print(f"  ok {lulus:2d}. {nama}")


print("== genesis ==")
bc = Blockchain()
cek("rantai baru berisi tepat 1 blok", len(bc.chain) == 1)
g = bc.chain[0]
cek("genesis: index 1", g['index'] == 1)
cek("genesis: proof 100", g['proof'] == 100)
cek("genesis: previous_hash 1 (int, persis panduan)",
    g['previous_hash'] == 1)
cek("genesis: transaksi kosong", g['transactions'] == [])
cek("genesis: timestamp float positif",
    isinstance(g['timestamp'], float) and g['timestamp'] > 0)
cek("last_block adalah genesis", bc.last_block is g)

print("== hash ==")
h1 = Blockchain.hash(g)
cek("hash: 64 heksadesimal", len(h1) == 64 and
    all(c in '0123456789abcdef' for c in h1))
cek("hash: deterministik", Blockchain.hash(dict(g)) == h1)
# Dict yang dibangun dengan urutan kunci berbeda harus ber-hash sama.
g_acakan = {'transactions': [], 'proof': 100, 'previous_hash': 1,
            'timestamp': g['timestamp'], 'index': 1}
cek("hash: tak peka urutan kunci (sort_keys)",
    Blockchain.hash(g_acakan) == h1)
g_ubah = dict(g, proof=101)
cek("hash: satu nilai berubah -> hash berubah",
    Blockchain.hash(g_ubah) != h1)
# Rumus hash ditulis ulang manual dari definisinya.
import json as _json
manual = hashlib.sha256(_json.dumps(g, sort_keys=True).encode()).hexdigest()
cek("hash: cocok dengan rumus manual json+sha256", manual == h1)

print("== transaksi & blok baru ==")
idx = bc.new_transaction("alice", "bob", 5)
cek("new_transaction mengembalikan index blok berikut (2)", idx == 2)
cek("transaksi mengantre", bc.current_transactions ==
    [{'sender': 'alice', 'recipient': 'bob', 'amount': 5}])
blok2 = bc.new_block(proof=35293)
cek("blok 2: index 2", blok2['index'] == 2)
cek("blok 2: memuat transaksi tadi", blok2['transactions'] ==
    [{'sender': 'alice', 'recipient': 'bob', 'amount': 5}])
cek("blok 2: previous_hash = hash(genesis)",
    blok2['previous_hash'] == Blockchain.hash(g))
cek("antrean transaksi tereset sesudah blok ditempa",
    bc.current_transactions == [])
cek("last_block kini blok 2", bc.last_block is blok2)

print("== proof of work: jangkar artikel ==")
cek("valid_proof(100, 35293) benar",
    Blockchain.valid_proof(100, 35293))
cek("valid_proof(35293, 35089) benar",
    Blockchain.valid_proof(35293, 35089))
cek("semua proof < 35293 untuk last_proof 100 tidak sah",
    not any(Blockchain.valid_proof(100, p)
            for p in (0, 1, 2, 100, 1000, 20000, 35292)))
p1 = bc.proof_of_work(100)
cek(f"proof_of_work(100) = 35293 persis artikel (dapat {p1})",
    p1 == 35293)
p2 = bc.proof_of_work(35293)
cek(f"proof_of_work(35293) = 35089 persis artikel (dapat {p2})",
    p2 == 35089)

print("== contoh mainan artikel (x=5) ==")
y = 0
while hashlib.sha256(f'{5 * y}'.encode()).hexdigest()[-1] != "0":
    y += 1
cek("y terkecil = 21", y == 21)
cek("hash(5*21) persis seperti dicetak artikel",
    hashlib.sha256(b'105').hexdigest() ==
    "1253e9373e781b7500266caa55150e08e210bc8cd8cc70d89985e3600155e860")

print(f"\nIRISAN 1 HIJAU: {lulus} pemeriksaan")
