from collections.abc import Hashable, Iterable
from typing import TypeAlias, TypeVar


Key: TypeAlias = Hashable
Row: TypeAlias = tuple[Key, int]
EnergyIndex: TypeAlias = dict[Key, int]

T = TypeVar("T")


def passthrough(data: T) -> T:
    return data


def prepare_energy(rows: Iterable[Row]) -> EnergyIndex:
    distinct_by_key: dict[Key, set[int]] = {}
    for key, value in rows:
        distinct_by_key.setdefault(key, set()).add(value)

    return {
        key: sum(value * value for value in distinct_values)
        for key, distinct_values in distinct_by_key.items()
    }
