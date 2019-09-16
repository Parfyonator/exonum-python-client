"""Module with the common cryptography-assotiated utils.

This module uses libsodium as a backend."""
from typing import Optional

from pysodium import (
    crypto_sign_keypair,
    crypto_sign_detached,
    crypto_sign_verify_detached,
    crypto_hash_sha256,
    crypto_hash_sha256_BYTES,
    crypto_sign_SECRETKEYBYTES,
    crypto_sign_PUBLICKEYBYTES,
    crypto_sign_BYTES,
)

HASH_BYTES_LEN = crypto_hash_sha256_BYTES
PUBLIC_KEY_BYTES_LEN = crypto_sign_PUBLICKEYBYTES
SECRET_KEY_BYTES_LEN = crypto_sign_SECRETKEYBYTES
SIGNATURE_BYTES_LEN = crypto_sign_BYTES

# Classes here not only used as a storage, but also contain verification, so it's OK.
# pylint: disable=too-few-public-methods


class _FixedByteArray:
    """Base class for types which store a bytes sequence of a fixed length."""

    def __init__(self, data: bytes, expected_len: int):
        if len(data) != expected_len:
            raise ValueError("Incorrect data length (expected {}, got {}".format(expected_len, len(data)))

        self.value = data

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _FixedByteArray):
            return False
        return self.value == other.value

    def __str__(self) -> str:
        # Represents the stored value as a hexadecimal string.
        return self.value.hex()


class Hash(_FixedByteArray):
    """Representation of the SHA-256 hash."""

    def __init__(self, hash_bytes: bytes):
        super().__init__(hash_bytes, HASH_BYTES_LEN)

    @classmethod
    def hash_data(cls, data: Optional[bytes]) -> "Hash":
        """Calculates the hash of provided bytes sequence and returns a Hash object.

        If `None` is provided, a hash of the empty sequence will be returned."""
        if data is not None:
            hash_bytes = crypto_hash_sha256(data)
        else:
            hash_bytes = crypto_hash_sha256(bytes())
        return cls(hash_bytes)

    def hex(self) -> str:
        """Returns hash as a hexadecimal string."""
        return self.value.hex()


class PublicKey(_FixedByteArray):
    """Representation of Curve25519 Public Key"""

    def __init__(self, key: bytes):
        super().__init__(key, PUBLIC_KEY_BYTES_LEN)


class SecretKey(_FixedByteArray):
    """Representation of Curve25519 Secret Key"""

    def __init__(self, key: bytes):
        super().__init__(key, SECRET_KEY_BYTES_LEN)


class KeyPair:
    """Representation of Curve25519 keypair"""

    def __init__(self, public_key: PublicKey, secret_key: SecretKey):
        # Check that public_key corresponds to the secret_key.
        # Since we're use only the libsodium backend, it's okay to check it like that.
        # libsodium secret key contains a public key inside.
        if secret_key.value[PUBLIC_KEY_BYTES_LEN:] != public_key.value:
            raise ValueError("Public key doesn't correspond to the secret key")

        self.public_key = public_key
        self.secret_key = secret_key

    @classmethod
    def generate(cls) -> "KeyPair":
        """Generates a new random keypair."""
        public_key, secret_key = crypto_sign_keypair()
        return cls(PublicKey(public_key), SecretKey(secret_key))


class Signature(_FixedByteArray):
    """Representation of Curve25519 signature"""

    def __init__(self, signature: bytes):
        super().__init__(signature, SIGNATURE_BYTES_LEN)

    @classmethod
    def sign(cls, data: bytes, key: SecretKey) -> "Signature":
        """Signs the provided bytes sequence with a provided secret key."""

        signature = crypto_sign_detached(data, key.value)

        return Signature(signature)

    def verify(self, data: bytes, key: PublicKey) -> bool:
        """Verifies the signature against provided data and public key."""

        try:
            crypto_sign_verify_detached(self.value, data, key.value)
            return True
        except ValueError:
            # ValueError is raised if verification is failed.
            return False
