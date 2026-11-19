# Uji irisan 4 — baterai akhir.
# 1) Regresi penuh irisan 1-3 sebagai subprocess.
# 2) Skenario ujung-ke-ujung dua node BARU (port 5003 & 5004):
#    transaksi pemakai di node C kalah fork dari rantai node D
#    yang lebih panjang (transaksi yatim hilang — pelajaran
#    jujur panduan), lalu C menambang di atas rantai adopsi
#    dan D ganti mengadopsi: lingkaran konsensus penuh.
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aset', 'lib'))

import requests

from blockchain import Blockchain

DIR = os.path.dirname(os.path.abspath(__file__))
lulus = 0


def cek(nama, kondisi):
    global lulus
    assert kondisi, f"GAGAL: {nama}"
    lulus += 1
    print(f"  ok {lulus:2d}. {nama}")


print("== regresi irisan 1-3 ==")
env = dict(os.environ,
           PYTHONPATH=os.path.join(DIR, 'aset', 'lib'))
for nama in ('uji_irisan1.py', 'uji_irisan2.py', 'uji_irisan3.py'):
    r = subprocess.run([sys.executable, nama], cwd=DIR, env=env,
                       capture_output=True, text=True)
    baris_akhir = r.stdout.strip().splitlines()[-1] if r.stdout else ''
    cek(f"{nama} hijau ({baris_akhir})",
        r.returncode == 0 and 'HIJAU' in baris_akhir)

print("== skenario fork & lingkaran konsensus ==")
procs = []
try:
    for port in (5003, 5004):
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

    tunggu(5003)
    tunggu(5004)
    C = 'http://localhost:5003'
    D = 'http://localhost:5004'

    # C menerima transaksi pemakai lalu menambangnya.
    r = requests.post(f'{C}/transactions/new', json={
        'sender': 'dompet-c', 'recipient': 'dompet-tujuan', 'amount': 7})
    cek("transaksi pemakai diterima C (201, Block 2)",
        r.status_code == 201
        and r.json()['message'] == "Transaction will be added to Block 2")
    requests.get(f'{C}/mine')
    rantai_c = requests.get(f'{C}/chain').json()
    cek("rantai C panjang 2 & memuat transaksi pemakai",
        rantai_c['length'] == 2
        and {'sender': 'dompet-c', 'recipient': 'dompet-tujuan',
             'amount': 7} in rantai_c['chain'][1]['transactions'])

    # D menambang sendirian sampai lebih panjang.
    for _ in range(3):
        requests.get(f'{D}/mine')
    cek("rantai D panjang 4",
        requests.get(f'{D}/chain').json()['length'] == 4)

    # C mengadopsi rantai D: transaksi C menjadi yatim.
    requests.post(f'{C}/nodes/register', json={'nodes': [D]})
    r = requests.get(f'{C}/nodes/resolve')
    cek("C mengadopsi rantai D",
        r.json()['message'] == 'Our chain was replaced')
    rantai_c = requests.get(f'{C}/chain').json()
    cek("rantai C kini identik dengan D",
        rantai_c == requests.get(f'{D}/chain').json())
    semua_tx = [tx for b in rantai_c['chain'] for tx in b['transactions']]
    cek("transaksi yatim C hilang dari rantai kanonik",
        all(tx.get('sender') != 'dompet-c' for tx in semua_tx))

    # C menambang di atas rantai adopsi; D ganti mengadopsi.
    requests.get(f'{C}/mine')
    cek("C panjang 5 sesudah menambang di rantai adopsi",
        requests.get(f'{C}/chain').json()['length'] == 5)
    requests.post(f'{D}/nodes/register', json={'nodes': [C]})
    r = requests.get(f'{D}/nodes/resolve')
    cek("D kini mengadopsi rantai C",
        r.json()['message'] == 'Our chain was replaced')
    cek("kedua rantai identik lagi (lingkaran penuh)",
        requests.get(f'{C}/chain').json()
        == requests.get(f'{D}/chain').json())

    # Rantai final lolos valid_chain dari instance lokal bersih.
    rantai_final = requests.get(f'{C}/chain').json()['chain']
    cek("rantai final 5 blok sah menurut valid_chain lokal",
        Blockchain().valid_chain(rantai_final))
finally:
    for p in procs:
        p.terminate()
    for p in procs:
        p.wait(timeout=5)

print(f"\nIRISAN 4 HIJAU: {lulus} pemeriksaan")
