from __future__ import annotations

import math


def hashed_embedding(text: str, dimensions: int = 48) -> list[float]:
    vector = [0.0] * dimensions
    for token in text.lower().split():
        slot = hash(token) % dimensions
        vector[slot] += 1.0

    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / magnitude, 6) for value in vector]

