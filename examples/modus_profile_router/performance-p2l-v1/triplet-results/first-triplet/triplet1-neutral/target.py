def answer(rows, queries):
    values_by_key = {}
    for key, value in rows:
        values_by_key.setdefault(key, set()).add(value)

    energy_by_key = {
        key: sum(value * value for value in values)
        for key, values in values_by_key.items()
    }
    return [energy_by_key.get(query, 0) for query in queries]
