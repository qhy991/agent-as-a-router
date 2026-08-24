def answer(rows, queries):
    return [sum({value for key, value in rows if key == query}) for query in queries]
