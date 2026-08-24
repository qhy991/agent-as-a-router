from collections.abc import Hashable, Iterable, Sized

from .shared import passthrough


def prepare_input(data: Iterable[tuple[Hashable, int]]) -> dict[Hashable, int]:
    return passthrough(data)


def describe(data: Sized) -> int:
    return len(data)
