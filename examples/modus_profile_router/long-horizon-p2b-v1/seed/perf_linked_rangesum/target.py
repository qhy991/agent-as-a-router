def answer(values, queries):
    size = len(values)
    result = []
    for start, stop in queries:
        left = max(0, min(size, start))
        right = max(0, min(size, stop))
        result.append(sum(values[left:right]) if left < right else 0)
    return result
