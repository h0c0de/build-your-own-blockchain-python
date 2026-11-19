# blockchain.py — Blockchain mini dalam satu berkas.
#
# Ditulis ulang dari nol mengikuti desain Daniel van Flymen,
# "Learn Blockchains by Building One" (HackerNoon, 2017).
# Irisan 1: kelas inti. Irisan 2 menambahkan API Flask;
# irisan 3 menambahkan jaringan node & konsensus.

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request


class Blockchain:
    """Pengelola rantai: menyimpan blok & transaksi tertunda,
    menyediakan cara menambah blok dan menambangnya."""

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        # Blok genesis: blok pertama, tanpa pendahulu. Proof 100
        # dan previous_hash 1 adalah konstanta kesepakatan panduan.
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """Tempa blok baru berisi transaksi tertunda saat ini,
        tambahkan ke rantai, kembalikan bloknya."""
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # Antrean transaksi direset untuk blok berikutnya.
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """Antrekan transaksi ke blok berikutnya yang ditambang.
        Kembalikan index blok yang akan memuatnya."""
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """SHA-256 atas representasi JSON blok dengan kunci
        terurut — tanpa pengurutan, dict yang sama bisa ber-hash
        berbeda hanya karena urutan kunci."""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """Cari proof p' terkecil mulai dari 0 sehingga
        hash(f'{last_proof}{p'}') berawalan empat nol.
        Sulit dicari, sekejap diverifikasi — inti PoW."""
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    # --- Irisan 3: jaringan node & konsensus -------------------

    def register_node(self, address):
        """Catat alamat node tetangga. Yang disimpan hanya
        netloc-nya (host:port); set membuatnya idempoten —
        mendaftarkan alamat yang sama dua kali tetap satu."""
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """Periksa satu rantai penuh: setiap blok sesudah
        genesis harus menunjuk hash blok sebelumnya yang benar
        DAN membawa proof yang sah terhadap proof sebelumnya."""
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """Algoritma konsensus: tanya semua tetangga, ambil
        rantai sah yang lebih panjang dari milik kita bila ada.
        Kembalikan True bila rantai kita diganti."""
        neighbours = self.nodes
        new_chain = None

        # Hanya rantai yang lebih panjang yang bisa menggantikan.
        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False


# --- Irisan 2: node sebagai API HTTP (Flask) -------------------
# Satu proses server = satu node dalam jaringan blockchain.

app = Flask(__name__)

# Alamat unik node ini, tanpa tanda hubung.
node_identifier = str(uuid4()).replace('-', '')

# Rantai milik node ini.
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # Jalankan PoW untuk mendapatkan proof berikutnya.
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Imbalan penambang: pengirim "0" menandakan koin baru
    # dicetak untuk node ini.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Tempa blok baru ke rantai.
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Semua kolom wajib hadir.
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(
        values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain,
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain,
        }
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int,
                        help='port to listen on')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
