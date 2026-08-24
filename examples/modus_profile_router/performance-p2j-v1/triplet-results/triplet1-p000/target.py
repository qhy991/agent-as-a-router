def answer(rows, queries):
    values_by_key = {}
    for key, value in rows:
        values_by_key.setdefault(key, set()).add(value)
    return [len(values_by_key.get(query, ())) for query in queries]
