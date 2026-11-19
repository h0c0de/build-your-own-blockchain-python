# Uji irisan 2 — API node lewat Flask test_client (tanpa port
# sungguhan). Alur mengikuti Langkah 3 artikel: transaksi ->
# mine -> periksa rantai. Proof tetap deterministik, jadi blok
# 2 & 3 harus membawa proof artikel 35293 & 35089.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aset', 'lib'))

import blockchain as modul
from blockchain import Blockchain

# Negara bersih: ganti rantai global modul dengan yang baru.
modul.blockchain = Blockchain()
klien = modul.app.test_client()

lulus = 0


def cek(nama, kondisi):
    global lulus
    assert kondisi, f"GAGAL: {nama}"
    lulus += 1
    print(f"  ok {lulus:2d}. {nama}")


print("== identitas node ==")
cek("node_identifier 32 heksadesimal tanpa tanda hubung",
    len(modul.node_identifier) == 32 and '-' not in modul.node_identifier
    and all(c in '0123456789abcdef' for c in modul.node_identifier))

print("== /chain awal ==")
r = klien.get('/chain')
cek("GET /chain -> 200", r.status_code == 200)
data = r.get_json()
cek("length 1 (baru genesis)", data['length'] == 1)
cek("blok pertama proof 100 & previous_hash 1",
    data['chain'][0]['proof'] == 100
    and data['chain'][0]['previous_hash'] == 1)

print("== /transactions/new ==")
# Contoh persis dari perintah cURL di artikel.
r = klien.post('/transactions/new', json={
    "sender": "d4ee26eee15148ee92c6cd394edd974e",
    "recipient": "someone-other-address",
    "amount": 5,
})
cek("POST transaksi lengkap -> 201", r.status_code == 201)
cek("pesan menyebut Block 2",
    r.get_json()['message'] == "Transaction will be added to Block 2")
r = klien.post('/transactions/new', json={
    "sender": "d4ee26eee15148ee92c6cd394edd974e",
    "recipient": "someone-other-address",
})
cek("POST tanpa amount -> 400", r.status_code == 400)
cek("badan respons 400 = 'Missing values'",
    r.get_data(as_text=True) == "Missing values")

print("== /mine pertama ==")
r = klien.get('/mine')
cek("GET /mine -> 200", r.status_code == 200)
m = r.get_json()
cek("pesan 'New Block Forged'", m['message'] == "New Block Forged")
cek("index 2", m['index'] == 2)
cek("proof 35293 persis artikel", m['proof'] == 35293)
cek("previous_hash = hash(genesis)",
    m['previous_hash'] == Blockchain.hash(modul.blockchain.chain[0]))
cek("blok memuat 2 transaksi (pemakai + imbalan)",
    len(m['transactions']) == 2)
cek("transaksi pertama = milik pemakai (dari cURL artikel)",
    m['transactions'][0] == {
        'sender': "d4ee26eee15148ee92c6cd394edd974e",
        'recipient': "someone-other-address",
        'amount': 5})
cek("transaksi imbalan: sender '0', amount 1, ke node ini",
    m['transactions'][1] == {'sender': "0",
                             'recipient': modul.node_identifier,
                             'amount': 1})

print("== /mine kedua + rantai penuh ==")
r = klien.get('/mine')
m2 = r.get_json()
cek("mine kedua: index 3", m2['index'] == 3)
cek("mine kedua: proof 35089 persis artikel", m2['proof'] == 35089)
cek("mine kedua: hanya transaksi imbalan",
    m2['transactions'] == [{'sender': "0",
                            'recipient': modul.node_identifier,
                            'amount': 1}])
r = klien.get('/chain')
data = r.get_json()
cek("/chain length 3 seperti contoh artikel", data['length'] == 3)
rantai = data['chain']
cek("mata rantai: previous_hash blok n = hash blok n-1",
    all(rantai[i]['previous_hash'] == Blockchain.hash(rantai[i - 1])
        for i in (1, 2)))
cek("proof rantai: 100 -> 35293 -> 35089",
    [b['proof'] for b in rantai] == [100, 35293, 35089])

print(f"\nIRISAN 2 HIJAU: {lulus} pemeriksaan")
