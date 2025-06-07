import math
from typing import Self


class Vector(complex):
    def __add__(self, other) -> Self:
        return Vector(super().__add__(other))

    def __sub__(self, other) -> Self:
        return Vector(super().__sub__(other))

    def __mul__(self, other) -> Self:
        return Vector(super().__mul__(other))

    def __truediv__(self, other) -> Self:
        return Vector(super().__truediv__(other))

    def __neg__(self):
        return Vector(super().__neg__())

    @property
    def unit(self) -> Self:
        return self / l if (l := abs(self)) != 0 else Vector(0)

    @property
    def angle(self) -> float:
        return math.atan2(self.y, self.x)

    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y

    def rotate(self, angle) -> Self:
        return self * Vector(math.cos(angle), math.sin(angle))

    x = complex.real
    y = complex.imag
