def moving_average(values, window):
    """Mutant: the 'window larger than the data' check is gone."""
    if window <= 0:
        raise ValueError("window must be positive")
    return [sum(values[i:i + window]) / window for i in range(len(values) - window + 1)]
