def answer(config, queries):
    result = []
    for query in queries:
        rotation, mask, multiplier, offset, modulus = config
        rotation %= 32
        multiplier %= modulus
        offset %= modulus
        value = query & 0xffffffff
        rotated = ((value << rotation) | (value >> (32 - rotation))) & 0xffffffff if rotation else value
        result.append(((rotated ^ mask) * multiplier + offset) % modulus)
    return result
