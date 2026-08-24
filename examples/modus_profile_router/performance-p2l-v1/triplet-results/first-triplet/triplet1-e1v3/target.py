def answer(energy_by_key, queries):
    return [energy_by_key.get(query, 0) for query in queries]
