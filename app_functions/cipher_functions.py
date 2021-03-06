#!/usr/bin/env python
"""
Cipher functions for the Habitica To Do Over tool.
"""
from __future__ import print_function
from __future__ import absolute_import

__author__ = "Katie Patterson kirska.com"
__license__ = "MIT"

import os.path

from cryptography.fernet import Fernet

from config import ProdConfig, DevConfig

if 'ENV' in os.environ and os.getenv('ENV') == 'prod':
    CIPHER_FILE = ProdConfig.CIPHER_FILE
else:
    CIPHER_FILE = DevConfig.CIPHER_FILE


def generate_cipher_key():
    """Generates a cipher key.

    Generates a cipher key to be used for storing
    sensitive data in the database.
    This will make all existing data GARBAGE so use with caution.
    """
    key = Fernet.generate_key()
    with open(CIPHER_FILE, 'wb') as cipher_file:
        cipher_file.write(key)


def encrypt_text(text):
    """Encrypt some text using the cipher key.

    Read the cipher key from file and use it to encrypt some text.

    Args:
        text: the text to be encrypted.

    Returns:
        The encrypted text.
    """
    with open(CIPHER_FILE, 'rb') as cipher_file:
        key = cipher_file.read()
        cipher_suite = Fernet(key)
        cipher_text = cipher_suite.encrypt(text)
        return cipher_text


def decrypt_text(cipher_text, cipher_file_path=CIPHER_FILE):
    """Decrypt some text back into the plain text.

    Read the cipher key from file and use it to decrypt some text.

    Args:
        cipher_text: the encrypted text we want to decrypt.
        cipher_file_path: optional specification of path to file.

    Returns:
        The decrypted text.
    """
    with open(cipher_file_path, 'rb') as cipher_file:
        key = cipher_file.read()
        cipher_suite = Fernet(key)
        plain_text = cipher_suite.decrypt(cipher_text)
        return plain_text


def test_cipher(test_text):
    """Test the cipher functions.

    Encrypt and then decrypt some text using the cipher stored
    in the cipher file.

    Args:
        test_text: some plain text we want to test encrypting and decrypting.
    """
    cipher_text = encrypt_text(test_text)
    print(cipher_text)
    plain_text = decrypt_text(cipher_text)
    print(plain_text)


def init_cipher_key():
    """Init the cipher key

    If cipher key has not created, then create a new one.

    """
    if not os.path.exists(CIPHER_FILE):
        generate_cipher_key()


if __name__ == '__main__':
    args = input('Please choose generate(input 1) or test(input 2) cipher\n')
    if args == 'generate' or args == 1:
        generate_cipher_key()
    elif args == 'test' or args == 2:
        test_cipher(input('Please input any Text:\n'))
