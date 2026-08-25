def answer(rows, queries):
    return [sum(value ** 4 for value in {value for key, value in rows if key == query}) for query in queries]
