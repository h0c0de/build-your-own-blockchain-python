# Uji irisan 3 — jaringan node & konsensus.
# Paruh unit: register_node + valid_chain (termasuk perusakan).
# Paruh hidup: DUA server sungguhan (subprocess, port 5001 &
# 5002) — node pendek mendaftar ke node panjang, memanggil
# resolve, dan rantainya harus diganti byte-identik.
import copy
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aset', 'lib'))

import requests

from blockchain import Blockchain

lulus = 0


def cek(nama, kondisi):
    global lulus
    assert kondisi, f"GAGAL: {nama}"
    lulus += 1
    print(f"  ok {lulus:2d}. {nama}")


def rantai_murni():
    """Rantai 3 blok hasil tambang sungguhan (proof artikel)."""
    bc = Blockchain()
    bc.new_transaction("0", "penambang", 1)
    bc.new_block(bc.proof_of_work(bc.last_block['proof']))
    bc.new_transaction("0", "penambang", 1)
    bc.new_block(bc.proof_of_work(bc.last_block['proof']))
    return bc


print("== register_node ==")
bc = Blockchain()
bc.register_node('http://192.168.0.5:5000')
cek("netloc yang disimpan", bc.nodes == {'192.168.0.5:5000'})
bc.register_node('http://192.168.0.5:5000')
cek("idempoten: daftar ulang tetap satu", len(bc.nodes) == 1)
bc.register_node('http://localhost:5001')
cek("node kedua tercatat", bc.nodes == {'192.168.0.5:5000', 'localhost:5001'})

print("== valid_chain ==")
bc = rantai_murni()
cek("rantai hasil tambang sendiri sah", bc.valid_chain(bc.chain))
cek("rantai genesis-saja sah", bc.valid_chain(bc.chain[:1]))

rusak_tengah = copy.deepcopy(bc.chain)
rusak_tengah[1]['transactions'][0]['amount'] = 1000
cek("ubah amount di blok TENGAH -> tidak sah",
    not bc.valid_chain(rusak_tengah))

rusak_proof = copy.deepcopy(bc.chain)
rusak_proof[2]['proof'] = 35090
cek("ubah proof blok terakhir -> tidak sah",
    not bc.valid_chain(rusak_proof))

rusak_tunjuk = copy.deepcopy(bc.chain)
rusak_tunjuk[2]['previous_hash'] = '0' * 64
cek("ubah previous_hash -> tidak sah",
    not bc.valid_chain(rusak_tunjuk))

# Temuan jujur: valid_chain memeriksa TUNJUKAN & proof tiap
# blok, bukan hash isi blok terakhir itu sendiri — jadi isi
# blok UJUNG yang diubah masih lolos... sampai ada blok
# berikutnya yang menunjuk hash aslinya.
rusak_ujung = copy.deepcopy(bc.chain)
rusak_ujung[2]['transactions'][0]['amount'] = 1000
cek("ubah amount di blok UJUNG -> masih lolos (celah ujung)",
    bc.valid_chain(rusak_ujung))
bc4 = rantai_murni()
bc4.new_transaction("0", "penambang", 1)
blok4 = bc4.new_block(bc4.proof_of_work(bc4.last_block['proof']))
rantai4_rusak = copy.deepcopy(bc4.chain)
rantai4_rusak[2]['transactions'][0]['amount'] = 1000
cek("sesudah ada blok 4, kerusakan blok 3 yang sama tertangkap",
    not bc4.valid_chain(rantai4_rusak))

print("== konsensus dua server hidup ==")
DIR = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, PYTHONPATH=os.path.join(DIR, 'aset', 'lib'))
procs = []
try:
    for port in (5001, 5002):
        p = subprocess.Popen(
            [sys.executable, 'blockchain.py', '-p', str(port)],
            cwd=DIR, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(p)

    def tunggu(port):
        for _ in range(100):
            try:
                r = requests.get(f'http://localhost:{port}/chain', timeout=1)
                if r.status_code == 200:
                    return
            except requests.RequestException:
                pass
            time.sleep(0.1)
        raise RuntimeError(f"server port {port} tidak menyala")

    tunggu(5001)
    tunggu(5002)
    cek("kedua server menyala", True)

    A = 'http://localhost:5001'
    B = 'http://localhost:5002'
    # Node B menambang 2 blok; node A diam di genesis.
    requests.get(f'{B}/mine')
    requests.get(f'{B}/mine')
    cek("B panjang 3, A panjang 1",
        requests.get(f'{B}/chain').json()['length'] == 3
        and requests.get(f'{A}/chain').json()['length'] == 1)

    r = requests.post(f'{A}/nodes/register', json={'nodes': [B]})
    cek("register di A -> 201", r.status_code == 201)
    cek("total_nodes A memuat localhost:5002",
        r.json()['total_nodes'] == ['localhost:5002'])
    r = requests.post(f'{A}/nodes/register', json={})
    cek("register tanpa daftar nodes -> 400", r.status_code == 400)

    r = requests.get(f'{A}/nodes/resolve')
    cek("resolve A: 'Our chain was replaced'",
        r.json()['message'] == 'Our chain was replaced')
    cek("rantai A kini byte-identik dengan rantai B",
        requests.get(f'{A}/chain').json()
        == requests.get(f'{B}/chain').json())

    r = requests.get(f'{A}/nodes/resolve')
    cek("resolve A kedua: 'Our chain is authoritative'",
        r.json()['message'] == 'Our chain is authoritative')

    requests.post(f'{B}/nodes/register', json={'nodes': [A]})
    r = requests.get(f'{B}/nodes/resolve')
    cek("resolve B (sama panjang): authoritative, tidak diganti",
        r.json()['message'] == 'Our chain is authoritative')
finally:
    for p in procs:
        p.terminate()
    for p in procs:
        p.wait(timeout=5)

print(f"\nIRISAN 3 HIJAU: {lulus} pemeriksaan")
