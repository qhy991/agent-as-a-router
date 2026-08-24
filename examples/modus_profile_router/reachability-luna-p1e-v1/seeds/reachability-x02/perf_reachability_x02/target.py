def _reachable(edges, source, target):
    if source == target:
        return True
    frontier = [source]
    seen = {source}
    while frontier:
        node = frontier.pop()
        for left, right in edges:
            if left == node and right not in seen:
                if right == target:
                    return True
                seen.add(right)
                frontier.append(right)
    return False


def answer(edges, queries):
    return [_reachable(edges, source, target) for source, target in queries]
