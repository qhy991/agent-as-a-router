def answer(rows, queries):
    values_by_key = {}
    for key, value in rows:
        values = values_by_key.get(key)
        if values is None:
            values_by_key[key] = {value}
        else:
            values.add(value)

    return [len(values_by_key.get(query, ())) for query in queries]
