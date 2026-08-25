def answer(config, queries):
    rotation, mask, multiplier, offset, modulus = config
    rotation %= 32
    result = []
    for query in queries:
        value = query & 0xffffffff
        rotated = ((value << rotation) | (value >> (32 - rotation))) & 0xffffffff if rotation else value
        result.append(((rotated ^ mask) * multiplier + offset) % modulus)
    return result
