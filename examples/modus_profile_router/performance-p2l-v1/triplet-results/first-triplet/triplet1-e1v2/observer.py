from collections.abc import Iterable, Sized

from .shared import Row, passthrough, prepare_energy


def prepare_input(data: Iterable[Row]) -> Iterable[Row]:
    prepare_energy(data)
    return passthrough(data)


def describe(data: Sized) -> int:
    return len(data)
