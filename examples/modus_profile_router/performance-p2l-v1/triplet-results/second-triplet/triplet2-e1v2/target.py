from collections.abc import Hashable, Iterable

from .shared import PreparedEnergy


def answer(prepared: PreparedEnergy, queries: Iterable[Hashable]) -> list[int]:
    return [prepared.get(query, 0) for query in queries]
