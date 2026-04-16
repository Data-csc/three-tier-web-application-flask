import time
import threading


class RateLimiter:
    """Token bucket rate limiter for per-key rate limiting.

    The token bucket algorithm allows bursts up to the bucket capacity
    while maintaining a steady refill rate over time.
    """

    def __init__(self, rate_per_second, burst):
        """Initialize the rate limiter.

        Args:
            rate_per_second: Number of tokens to add per second (refill rate)
            burst: Maximum number of tokens in the bucket (burst capacity)
        """
        self.rate_per_second = float(rate_per_second)
        self.burst = int(burst)
        self.buckets = {}
        self.lock = threading.Lock()

    def allow(self, key):
        """Check if a request for the given key should be allowed.

        Args:
            key: Unique identifier (e.g., IP address)

        Returns:
            bool: True if request is allowed, False if rate limited
        """
        now = time.time()

        with self.lock:
            if key not in self.buckets:
                self.buckets[key] = {
                    'tokens': self.burst,
                    'last_refill': now
                }

            bucket = self.buckets[key]

            elapsed = now - bucket['last_refill']
            bucket['tokens'] = min(
                self.burst,
                bucket['tokens'] + elapsed * self.rate_per_second
            )
            bucket['last_refill'] = now

            if bucket['tokens'] >= 1.0:
                bucket['tokens'] -= 1.0
                return True

            return False

    def get_retry_after(self, key):
        """Calculate seconds until next token is available for the given key.

        Args:
            key: Unique identifier (e.g., IP address)

        Returns:
            int: Seconds to wait before retrying (ceiling value)
        """
        now = time.time()

        with self.lock:
            if key not in self.buckets:
                return 0

            bucket = self.buckets[key]

            elapsed = now - bucket['last_refill']
            bucket['tokens'] = min(
                self.burst,
                bucket['tokens'] + elapsed * self.rate_per_second
            )
            bucket['last_refill'] = now

            tokens_needed = 1.0 - bucket['tokens']

            if tokens_needed <= 0:
                return 0

            seconds = tokens_needed / self.rate_per_second
            return int(seconds) + 1
