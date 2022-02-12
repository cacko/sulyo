from hashlib import blake2b


def idhash(text, size=20):
    h = blake2b(digest_size=size)
    h.update(text.encode())
    return h.hexdigest()
