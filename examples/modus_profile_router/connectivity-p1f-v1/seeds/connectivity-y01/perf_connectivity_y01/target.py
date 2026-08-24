def _connected(edges, source, target):
    if source == target:
        return True
    frontier = [source]
    seen = {source}
    while frontier:
        node = frontier.pop()
        for left, right in edges:
            neighbor = right if left == node else left if right == node else None
            if neighbor is None or neighbor in seen:
                continue
            if neighbor == target:
                return True
            seen.add(neighbor)
            frontier.append(neighbor)
    return False


def answer(edges, queries):
    return [_connected(edges, source, target) for source, target in queries]
