from collections import Counter


def answer(tokens, queries):
    counts = Counter(tokens)
    return [counts.get(query, 0) for query in queries]
