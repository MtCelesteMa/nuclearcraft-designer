"""Multidimensional lists."""

import typing


E = typing.TypeVar("E")


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
