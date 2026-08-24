from collections.abc import Hashable, Iterable


def passthrough(data: Iterable[tuple[Hashable, int]]) -> dict[Hashable, int]:
    seen_values: dict[Hashable, set[int]] = {}
    energy_by_key: dict[Hashable, int] = {}
    for key, value in data:
        values = seen_values.setdefault(key, set())
        if value not in values:
            values.add(value)
            energy_by_key[key] = energy_by_key.get(key, 0) + value * value
    return energy_by_key
