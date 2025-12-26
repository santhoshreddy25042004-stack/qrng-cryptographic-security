from crypto.key_generation import generate_qrng_key
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

def send(message, key):
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv, cipher.encrypt(pad(message, AES.block_size))

def receive(iv, ciphertext, key):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)

def main():
    print("\n🔐 MODULE-3: Secure Communication using QRNG\n")

    shared_key = generate_qrng_key(256)
    message = b"Quantum-secured communication channel"

    iv, encrypted = send(message, shared_key)
    decrypted = receive(iv, encrypted, shared_key)

    print("Encrypted:", encrypted)
    print("Decrypted:", decrypted)
    print("\n✅ Secure communication established")

if __name__ == "__main__":
    main()
