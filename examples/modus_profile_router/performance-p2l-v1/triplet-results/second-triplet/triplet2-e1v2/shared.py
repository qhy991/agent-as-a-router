from collections.abc import Hashable, Iterable
from typing import TypeAlias


Row: TypeAlias = tuple[Hashable, int]
PreparedEnergy: TypeAlias = dict[Hashable, int]


def prepare_energy(rows: Iterable[Row]) -> PreparedEnergy:
    values_by_key: dict[Hashable, set[int]] = {}
    for key, value in rows:
        values_by_key.setdefault(key, set()).add(value)

    return {
        key: sum(value * value for value in values)
        for key, values in values_by_key.items()
    }
