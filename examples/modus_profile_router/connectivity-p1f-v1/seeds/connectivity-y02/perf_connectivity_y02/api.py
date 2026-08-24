from . import observer, target


def execute(data, query_batches):
    prepared = observer.prepare_input(data)
    return [target.answer(prepared, batch) for batch in query_batches]
