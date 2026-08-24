def answer(config, queries):
    multiplier, offset, modulus = config
    return [(query * multiplier + offset) % modulus for query in queries]
