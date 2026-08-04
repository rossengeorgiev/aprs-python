"""
APRS Duplicate Detection utilities.

Provides:
- dedup_key(): Extract canonical identity for duplicate comparison
- DuplicateFilter: Stateful filter that marks packets as duplicates

Based on the approach from perl-aprs-fap's aprs_duplicate_parts():
unwrap third-party layers, normalize source (with SSID), strip
destination SSID, and trim body whitespace.
"""

import time

__all__ = ['dedup_key', 'DuplicateFilter']


def dedup_key(packet):
    """
    Extract a canonical deduplication key from a raw APRS packet string.

    The key is a string of format "SOURCE:DESTINATION:BODY" where:
    - SOURCE has SSID normalized (bare call gets -0)
    - DESTINATION has SSID stripped
    - BODY has trailing whitespace removed
    - Third-party wrapping is recursively unwrapped

    Args:
        packet: Raw APRS packet string (e.g., "SRC>DST,PATH:body")

    Returns:
        String key for duplicate comparison, or None if packet is unparseable.
    """
    if not packet:
        return None

    # Unwrap third-party layers recursively
    while True:
        try:
            _header, body = packet.split(':', 1)
        except ValueError:
            return None
        if body.startswith('}'):
            packet = body[1:]
        else:
            break

    # Now parse the final unwrapped packet
    try:
        header, body = packet.split(':', 1)
    except ValueError:
        return None

    # Parse source>destination
    try:
        source, rest = header.split('>', 1)
    except ValueError:
        return None

    # Destination is first element (strip path)
    parts = rest.split(',', 1)
    destination = parts[0]

    # Normalize source: add -0 if no SSID
    if '-' not in source:
        source = source.upper() + '-0'
    else:
        source = source.upper()

    # Strip SSID from destination
    if '-' in destination:
        destination = destination.split('-', 1)[0]
    destination = destination.upper()

    # Trim trailing whitespace from body
    body = body.rstrip()

    return f"{source}:{destination}:{body}"


class DuplicateFilter:
    """
    Stateful duplicate packet filter.

    Tracks seen packets by their dedup_key and marks duplicates.
    Never drops packets — only annotates them with 'is_duplicate'.

    Usage:
        df = DuplicateFilter(ttl=28)
        parsed = aprslib.parse(packet)
        df.check(parsed)
        if parsed.get('is_duplicate'):
            # handle duplicate
    """

    def __init__(self, ttl=28):
        """
        Initialize the filter.

        Args:
            ttl: Time-to-live in seconds for duplicate window (default: 28s)
        """
        self.ttl = ttl
        self._seen = {}  # key -> timestamp

    def check(self, parsed):
        """
        Check a parsed packet dict for duplicates and annotate it.

        Adds 'dedup_key' and 'is_duplicate' fields to the parsed dict.

        Args:
            parsed: Dict from aprslib.parse() — must contain 'raw' key.

        Returns:
            True if duplicate, False if new.
        """
        raw = parsed.get('raw', '')
        key = dedup_key(raw)

        if key is None:
            parsed['dedup_key'] = None
            parsed['is_duplicate'] = False
            return False

        parsed['dedup_key'] = key
        now = time.time()

        # Prune expired entries (lazy cleanup)
        self._prune(now)

        if key in self._seen:
            parsed['is_duplicate'] = True
            # Update timestamp (sliding window)
            self._seen[key] = now
            return True
        else:
            parsed['is_duplicate'] = False
            self._seen[key] = now
            return False

    def _prune(self, now):
        """Remove entries older than TTL."""
        expired = [k for k, t in self._seen.items() if now - t > self.ttl]
        for k in expired:
            del self._seen[k]

    def clear(self):
        """Clear all tracked entries."""
        self._seen.clear()

    @property
    def size(self):
        """Number of tracked entries."""
        return len(self._seen)
