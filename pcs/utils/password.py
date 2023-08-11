import passlib.context

DEFAULT_CRYPT_CONTEXT = passlib.context.CryptContext(['pbkdf2_sha512', 'plaintext'], deprecated=['plaintext'])


def check_password(password, hashed):
    valid = DEFAULT_CRYPT_CONTEXT.verify(password, hashed)
    if not valid:
        return False

    return True


def encrypt_password(password):
    return DEFAULT_CRYPT_CONTEXT.encrypt(password)