def answer(rows, queries):
    distinct_by_key = {}
    for key, value in rows:
        values = distinct_by_key.get(key)
        if values is None:
            values = set()
            distinct_by_key[key] = values
        values.add(value)

    return [len(distinct_by_key.get(query, ())) for query in queries]
