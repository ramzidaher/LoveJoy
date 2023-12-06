from cryptography.fernet import Fernet

# Generate a key (do this once and store it securely)
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Encrypt
encrypted_text = cipher_suite.encrypt(b"Your sensitive data")
# Decrypt
decrypted_text = cipher_suite.decrypt(encrypted_text)

print("Encrypted:", encrypted_text)
print("Decrypted:", decrypted_text)
