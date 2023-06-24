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
            key[i] * math.prod(self.dims[:i])
            for i in range(len(self.dims))
        ])]


class Sequence2D(typing.Generic[E], typing.Iterable[E]):
    """Two-Dimensional Sequence."""
    def __init__(self, rep: list[E], cols: int) -> None:
        """

        :param rep:
        :param cols:
        """
        self.rep = rep
        self.cols = cols

    @property
    def rows(self) -> int:
        return len(self.rep) // self.cols

    def __len__(self) -> int:
        """Get the total number of elements

        :return:
        """
        return len(self.rep)

    def __iter__(self) -> typing.Iterable[E]:
        return iter(self.rep)

    def __getitem__(self, key: int | tuple[int, int]) -> E:
        """

        :param key:
        :return:
        """
        if isinstance(key, int):
            return self.rep[key]
        return self.rep[key[1] * self.cols + key[0]]
