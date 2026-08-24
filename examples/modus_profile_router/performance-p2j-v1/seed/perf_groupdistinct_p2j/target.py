def answer(rows, queries):
    return [len({value for key, value in rows if key == query}) for query in queries]
