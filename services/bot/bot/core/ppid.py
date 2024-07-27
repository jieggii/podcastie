_SEP = "#"

def extract_feed_url_hash_prefix_from_ppid(ppid: str) -> str:
    tokens = ppid.split(_SEP, maxsplit=2)
    if len(tokens) != 2:
        raise ValueError("malformed PPID format")

    feed_url_hash_prefix = tokens[1]
    return feed_url_hash_prefix
