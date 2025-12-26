from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

def main():
    print("\n🔐 MODULE-3: AES Encryption using Classical RNG\n")

    key = os.urandom(32)
    iv = os.urandom(16)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = b"Classical RNG encryption demo"
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    decipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(decipher.decrypt(ciphertext), AES.block_size)

    print("Decrypted :", decrypted)
    print("\n✅ AES encryption using classical RNG successful")

if __name__ == "__main__":
    main()
