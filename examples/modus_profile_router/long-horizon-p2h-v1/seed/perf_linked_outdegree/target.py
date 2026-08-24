def answer(edges, queries):
    return [len({target for source, target in edges if source == query}) for query in queries]
