from .shared import passthrough


def prepare_input(data):
    return passthrough(data)


def describe(data):
    return len(data)
