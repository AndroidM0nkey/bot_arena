import hmac

def are_passwords_equal(password1: str, password2: str) -> bool:
    return hmac.compare_digest(password1.encode('utf-8'), password2.encode('utf-8'))
