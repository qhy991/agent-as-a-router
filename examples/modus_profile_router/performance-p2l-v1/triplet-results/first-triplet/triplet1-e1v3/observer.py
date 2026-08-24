from .shared import passthrough


def prepare_input(data):
    prepared = passthrough(data)
    return prepared


def describe(data):
    return len(data)
