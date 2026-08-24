def answer(rows, queries):
    return [max((value for key, value in rows if key == query), default=None) for query in queries]
