"""Multidimensional sequences."""

from collections import abc
import math


class MultiSequence[E](abc.Sequence[E], abc.Iterable[E]):
    """A multidimensional Sequence."""
    def __init__(self, seq: abc.Sequence[E], dims: tuple[int, ...]) -> None:
        """Constructs a MultiSequence object.

        :param seq: A one-dimensional representation of the sequence.
        :param dims: The dimensions of the sequence.
        """
        self.seq = seq
        self.dims = dims
        assert math.prod(self.dims) == len(self.seq)

    def __iter__(self) -> abc.Iterator[E]:
        return iter(self.seq)

    def __len__(self) -> int:
        return len(self.seq)

    def int_to_tuple(self, key: int) -> tuple[int, ...]:
        """Converts an integer key to a tuple key.

        :param key: An integer key.
        :return: A tuple key.
        """
        return tuple([
            (key % math.prod(self.dims[i:])) // math.prod(self.dims[i + 1:])
            for i in range(len(self.dims))
        ])

    def tuple_to_int(self, key: tuple[int, ...]) -> int:
        """Converts a tuple key to an integer key.

        :param key: A tuple key.
        :return: An integer key.
        """
        return sum([
            key[i] * math.prod(self.dims[i + 1:])
            for i in range(len(self.dims))
        ])

    def __getitem__(self, key: int | tuple[int, ...]) -> E:
        if isinstance(key, int):
            return self.seq[key]
        return self.seq[self.tuple_to_int(key)]
