def paginate(items, page, page_size):
    """Return the items on a 1-based page."""
    start = page * page_size
    end = start + page_size
    return list(items[start:end])
