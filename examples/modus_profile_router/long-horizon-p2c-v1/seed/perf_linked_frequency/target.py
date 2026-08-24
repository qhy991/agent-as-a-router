def answer(tokens, queries):
    return [tokens.count(query) for query in queries]
