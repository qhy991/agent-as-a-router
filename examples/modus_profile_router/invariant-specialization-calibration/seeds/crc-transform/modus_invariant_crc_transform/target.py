def answer(config, sequences):
    polynomial, initial, xor_out = config
    result = []
    for sequence in sequences:
        crc = initial & 255
        for byte in sequence:
            crc ^= byte
            for _ in range(8):
                crc = ((crc << 1) ^ polynomial) & 255 if crc & 128 else (crc << 1) & 255
        result.append(crc ^ xor_out)
    return result
