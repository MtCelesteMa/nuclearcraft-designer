"""Multidimensional lists."""

import typing
import math


E = typing.TypeVar("E")


class MultiSequence(typing.Iterable[E]):
    """Multidimensional Sequence."""
    def __init__(self, seq: list[E], dims: tuple[int, ...]) -> None:
        """Constructs a MultiSequence object.

        :param seq: A one-dimensional representation of the sequence.
        :param dims: The dimensions of the sequence.
        """
        self.seq = seq
        self.dims = dims
        assert math.prod(self.dims) == len(self.seq)

    def __iter__(self) -> typing.Iterator[E]:
        return iter(self.seq)

    def __len__(self) -> int:
        return len(self.seq)

    def __getitem__(self, key: int | tuple[int, ...]) -> E:
        if isinstance(key, int):
            return self.seq[key]
        return self.seq[sum([
            key[i] * math.prod(self.dims[i + 1:])
            for i in range(len(self.dims))
        ])]
