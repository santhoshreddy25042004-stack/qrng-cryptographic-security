from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from crypto.key_generation import generate_qrng_key
import os

def main():
    print("\n🔐 MODULE-3: AES Encryption using QRNG Key\n")

    key = generate_qrng_key(256)
    iv = os.urandom(16)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = b"Quantum secure encryption demo"
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    print("Plaintext :", plaintext)
    print("Ciphertext:", ciphertext)

    decipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(decipher.decrypt(ciphertext), AES.block_size)

    print("Decrypted :", decrypted)
    print("\n✅ AES encryption using QRNG successful")

if __name__ == "__main__":
    main()
