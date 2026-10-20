def shipping_cost(weight_kg, zone, express=False):
    """Price in euro for one parcel."""
    if weight_kg <= 0:
        raise ValueError("weight must be positive")
    if zone == "local":
        if weight_kg <= 1:
            cost = 4.0
        elif weight_kg <= 5:
            cost = 6.5
        else:
            cost = 6.5 + (weight_kg - 5) * 1.2
    elif zone == "domestic":
        if weight_kg <= 1:
            cost = 7.0
        elif weight_kg <= 5:
            cost = 10.0
        else:
            cost = 10.0 + (weight_kg - 5) * 1.5
    elif zone == "international":
        if weight_kg <= 1:
            cost = 20.0
        elif weight_kg <= 5:
            cost = 32.0
        else:
            cost = 32.0 + (weight_kg - 5) * 4.0
    else:
        raise ValueError(f"unknown zone: {zone}")
    if express:
        cost = cost * 1.5
    return round(cost, 2)
