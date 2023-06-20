"""Optimizers for NuclearCraft designer."""

import copy
import typing


class OptimizableSequence:
    """An optimizable sequence."""
    def __init__(
            self,
            length: int,
            max_value: int,
            constraints: list[typing.Callable[[list[int]], bool]],
            scoring_func: typing.Callable[[list[int]], float]
    ) -> None:
        """Constructs an OptimizableSequence object.

        :param length: The length of the sequence.
        :param max_value: The maximum value of the sequence.
        :param constraints: A list of constraints the sequence must follow.
        :param scoring_func: A function used to score complete sequences.
        """
        self.length = length
        self.max_value = max_value
        self.constraints = constraints
        self.scoring_func = scoring_func

        self.sequence = [0 for _ in range(self.length)]

    def is_valid(self) -> bool:
        """Whether the sequence satisfies all constraints.

        :return: True if all constraints are satisfied, false otherwise.
        """
        for constraint in self.constraints:
            if not constraint(self.sequence):
                return False
        return True

    def advance(self) -> bool:
        """Advances the last value in the sequence if possible.

        :return: True if the operation was successful, false otherwise.
        """
        for i in range(self.length - 1, -1, -1):
            if self.sequence[i] != 0:
                if self.sequence[i] == self.max_value:
                    return False
                self.sequence[i] += 1
                return True
        return False

    def next_row(self) -> bool:
        """Adds a value to the sequence if possible.

        :return: True if the operation was successful, false otherwise.
        """
        for i in range(self.length):
            if self.sequence[i] == 0:
                self.sequence[i] = 1
                return True
        return False

    def prev_row(self) -> bool:
        """Removes the last value of the sequence and advances the sequence if possible.

        :return: True if the operation was successful, false otherwise.
        """
        for i in range(self.length - 1, -1, -1):
            if self.sequence[i] != 0:
                self.sequence[i] = 0
                if self.advance():
                    return True
                else:
                    return self.prev_row()
        return False

    def next_sequence(self) -> bool:
        """Finds the next candidate (partial) sequence if possible.

        :return: True if the operation was successful, false otherwise.
        """
        if self.is_valid():
            return self.next_row() or self.advance() or self.prev_row()
        else:
            return self.advance() or self.prev_row()

    def next_valid_sequence(self) -> bool:
        """Finds the next valid (partial) sequence if possible.

        :return: True if the operation was successful, false otherwise.
        """
        while True:
            if not self.next_sequence():
                return False
            if self.is_valid():
                return True

    def is_complete(self) -> bool:
        """Whether the sequence is complete.

        :return: True if the sequence is complete, false otherwise.
        """
        for elem in self.sequence:
            if elem == 0:
                return False
        return True

    def score(self) -> float:
        """Calculates the score of the sequence.

        :return: The score of the sequence.
        """
        return self.scoring_func(self.sequence)

    def optimize(self) -> bool:
        """Optimize the sequence.

        :return: True if an optimal sequence has been found, false otherwise.
        """
        opt_seq = None
        opt_score = -float('inf')

        while self.next_valid_sequence():
            if self.is_complete() and self.score() > opt_score:
                opt_seq = copy.deepcopy(self.sequence)
                opt_score = self.score()

        if opt_seq:
            self.sequence = opt_seq
            return True
        return False
