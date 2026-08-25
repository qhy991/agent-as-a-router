def answer(config, sequences):
    result = []
    for sequence in sequences:
        base, salt, modulus = config
        base %= modulus
        salt &= 255
        contributions = tuple(byte ^ salt for byte in range(256))
        value = 0
        for byte in sequence:
            value = (value * base + contributions[byte]) % modulus
        result.append(value)
    return result
