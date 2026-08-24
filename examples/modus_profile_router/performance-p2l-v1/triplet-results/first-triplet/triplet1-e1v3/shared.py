def passthrough(data):
    values_by_key = {}
    for key, value in data:
        values_by_key.setdefault(key, set()).add(value)
    return {
        key: sum(value * value for value in values)
        for key, values in values_by_key.items()
    }
