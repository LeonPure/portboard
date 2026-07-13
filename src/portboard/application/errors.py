"""Application-level failures that cannot be represented as partial results."""


class DiscoveryUnavailable(RuntimeError):
    """Raised when the operating-system listener scan cannot start."""
