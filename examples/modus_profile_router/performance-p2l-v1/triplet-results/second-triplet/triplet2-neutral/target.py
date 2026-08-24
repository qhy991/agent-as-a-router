from .shared import PreparedInput, prepare_energy


def answer(rows, queries):
    if not isinstance(rows, PreparedInput):
        rows = prepare_energy(rows)
    return [rows.get(query) for query in queries]
