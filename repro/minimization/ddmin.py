import math
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def minimize(
    sequence: list[T], reproduces: Callable[[list[T]], Awaitable[bool]], *, max_trials=12
) -> tuple[list[T], int]:
    """Bounded delta debugging. Every candidate is replayed from a fresh baseline."""
    current = list(sequence)
    granularity, trials = 2, 0
    while current and trials < max_trials:
        chunk_size = math.ceil(len(current) / granularity)
        reduced = False
        # UI experiments often continue inspecting after the first useful observation.
        # Try trailing chunks first; ordering never changes which deletions need proof.
        for start in reversed(range(0, len(current), chunk_size)):
            if trials >= max_trials:
                break
            candidate = current[:start] + current[start + chunk_size :]
            trials += 1
            if await reproduces(candidate):
                current = candidate
                granularity = max(2, granularity - 1)
                reduced = True
                break
        if not reduced:
            if granularity >= len(current):
                break
            granularity = min(len(current), granularity * 2)
    return current, trials
