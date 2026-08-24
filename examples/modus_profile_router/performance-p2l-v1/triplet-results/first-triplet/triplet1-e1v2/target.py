from collections.abc import Iterable, Mapping

from .shared import EnergyIndex, Key, Row, prepare_energy


def answer(rows: Iterable[Row] | EnergyIndex, queries: Iterable[Key]) -> list[int]:
    energy_by_key = rows if isinstance(rows, Mapping) else prepare_energy(rows)
    return [energy_by_key.get(query, 0) for query in queries]
