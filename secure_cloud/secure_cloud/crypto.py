# https://nitratine.net/blog/post/asymmetric-encryption-and-decryption-in-python/
# https://www.novixys.com/blog/using-aes-encryption-decryption-python-pycrypto/
# https://cryptography.io/en/

import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


CHUNK_SIZE = 64*1024
BLOCK_SIZE = 16


def generate_symmetric_key():
    key_length = 32
    # generate key using cryptographically secure pseudo-random number generator
    secret_key = os.urandom(key_length)
    return secret_key


def generate_keys(public_exponent, key_size, private_file, public_file):
    private_key = rsa.generate_private_key(
        public_exponent=public_exponent,
        key_size=key_size,
        backend=default_backend())

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())

    with open(private_file, "wb") as f:
        f.write(pem)

    public_key = private_key.public_key()
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)

    with open(public_file, "wb") as f:
        f.write(pem)


def encrypt_sym_key(public_key, sym_key):
    return public_key.encrypt(
        sym_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None))


def decrypt_sym_key(private_key, encrypted_sym_key):
    return private_key.decrypt(
        encrypted_sym_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None))


def encrypt_file(symmetric_key, input_file):
    file_size = (str(os.path.getsize(input_file)).zfill(BLOCK_SIZE))
    init_vector = os.urandom(BLOCK_SIZE)
    encryptor = Cipher(
        algorithms.AES(symmetric_key),
        modes.CBC(init_vector),
        backend=default_backend()
    ).encryptor()

    with open(input_file, "rb") as in_file:
        out_file  = ""
        out_file += file_size + "\n"
        out_file += str(init_vector)
        while True:
            chunk = in_file.read(CHUNK_SIZE)
            if len(chunk) == 0:
                break
            elif len(chunk) % BLOCK_SIZE != 0:
                # pad with spaces to make len(chunk) a multiple of 16
                chunk += b' ' * (BLOCK_SIZE - len(chunk) % BLOCK_SIZE)
            out_file += str(encryptor.update(chunk))
    return out_file


def decrypt_file(symmetric_key, input_file, output_file):
    with open(input_file, "rb") as in_file:
        file_size = int(in_file.read(BLOCK_SIZE))
        init_vector = in_file.read(BLOCK_SIZE)
        decryptor = Cipher(
            algorithms.AES(symmetric_key),
            modes.CBC(init_vector),
            backend=default_backend()
        ).decryptor()
        with open(output_file, "wb") as out_file:
            while True:
                chunk = in_file.read(CHUNK_SIZE)
                if len(chunk) == 0:
                    break
                out_file.write(decryptor.update(chunk))
            out_file.truncate(file_size)
