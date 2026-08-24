def _reachable_nodes(adjacency, source):
    reachable = {source}
    frontier = [source]
    while frontier:
        node = frontier.pop()
        for neighbor in adjacency.get(node, ()):
            if neighbor not in reachable:
                reachable.add(neighbor)
                frontier.append(neighbor)
    return reachable


def answer(edges, queries):
    adjacency = {}
    for source, target in edges:
        adjacency.setdefault(source, []).append(target)

    reachable_by_source = {}
    result = []
    for source, target in queries:
        if source == target:
            result.append(True)
            continue

        reachable = reachable_by_source.get(source)
        if reachable is None:
            reachable = _reachable_nodes(adjacency, source)
            reachable_by_source[source] = reachable
        result.append(target in reachable)
    return result
