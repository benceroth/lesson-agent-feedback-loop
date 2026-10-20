def moving_average(values, window):
    """Mutant: floor division truncates averages."""
    if window <= 0:
        raise ValueError("window must be positive")
    if window > len(values):
        raise ValueError("window is larger than the data")
    return [sum(values[i:i + window]) // window for i in range(len(values) - window + 1)]
