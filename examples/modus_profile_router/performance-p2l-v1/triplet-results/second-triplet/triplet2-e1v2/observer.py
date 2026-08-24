from collections.abc import Sized

from .shared import PreparedEnergy, Row, prepare_energy


def prepare_input(data: tuple[Row, ...]) -> PreparedEnergy:
    return prepare_energy(data)


def describe(data: Sized) -> int:
    return len(data)
