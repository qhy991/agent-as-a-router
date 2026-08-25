def answer(config, queries):
    coefficients, modulus = config
    result = []
    for query in queries:
        normalized = tuple(coefficient % modulus for coefficient in coefficients)
        value = 0
        for coefficient in normalized:
            value = (value * query + coefficient) % modulus
        result.append(value)
    return result
