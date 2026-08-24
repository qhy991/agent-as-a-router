def answer(config, queries):
    mask, multiplier, offset, modulus = config
    return [(((query ^ mask) * multiplier) + offset) % modulus for query in queries]
