def answer(rows, queries):
    return [max((value for key, value in rows if key == query and value < 0), default=None) for query in queries]
