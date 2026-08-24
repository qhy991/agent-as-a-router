class PreparedInput:
    __slots__ = ("energy_by_key",)

    def __init__(self, energy_by_key):
        self.energy_by_key = energy_by_key

    def get(self, key, default=0):
        return self.energy_by_key.get(key, default)


def prepare_energy(data):
    values_by_key = {}
    for key, value in data:
        values = values_by_key.get(key)
        if values is None:
            values_by_key[key] = {value}
        else:
            values.add(value)

    energy_by_key = {
        key: sum(value * value for value in values)
        for key, values in values_by_key.items()
    }
    return PreparedInput(energy_by_key)


def passthrough(data):
    return data
