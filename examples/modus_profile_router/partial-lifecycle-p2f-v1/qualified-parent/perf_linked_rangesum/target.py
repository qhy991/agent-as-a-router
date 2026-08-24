def answer(values, queries):
    prefix = [0]
    for value in values:
        prefix.append(prefix[-1] + value)
    prefix = tuple(prefix)
    size = len(values)
    result = []
    for start, stop in queries:
        left = max(0, min(size, start))
        right = max(0, min(size, stop))
        result.append(prefix[right] - prefix[left] if left < right else 0)
    return result
