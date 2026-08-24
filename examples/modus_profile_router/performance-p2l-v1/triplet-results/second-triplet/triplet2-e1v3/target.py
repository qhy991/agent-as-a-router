from collections.abc import Hashable, Iterable, Mapping


def answer(energy_by_key: Mapping[Hashable, int], queries: Iterable[Hashable]) -> list[int]:
    return [energy_by_key.get(query, 0) for query in queries]
