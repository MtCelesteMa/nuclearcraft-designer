"""Optimizers for NuclearCraft designer."""

import copy
import typing


class ConstrainedIntegerSequence:
    """A generator that generates a sequence of integers with constraints."""
    def __init__(self, length: int, upper_bound: int, constraints: list[typing.Callable[[list[int]], bool]]) -> None:
        """Constructs a ConstrainedIntegerSequence object.

        :param length: The length of the sequence.
        :param upper_bound: The upper bound. The sequence's values have a domain of [0, upper_bound).
        :param constraints: A list of constraints that the sequence must satisfy.
        """
        self.length = length
        self.upper_bound = upper_bound
        self.constraints = constraints

    def is_valid(self, sequence: list[int]) -> bool:
        """Whether the sequence satisfies all constraints.

        :param sequence: The sequence to be checked.
        :return: True if all constraints are satisfied, false otherwise.
        """
        for constraint in self.constraints:
            if not constraint(sequence):
                return False
        return True

    def is_complete(self, sequence: list[int]) -> bool:
        """Whether the sequence is complete.

        :return: True if the sequence is complete, false otherwise.
        """
        for elem in sequence:
            if elem == -1:
                return False
        return True

    def advance(self, sequence: list[int]) -> bool:
        """Advances the last value in the sequence if possible.

        :param sequence: The sequence to be modified.
        :return: True if the operation is successful, false otherwise.
        """
        for i in range(len(sequence) - 1, -1, -1):
            if sequence[i] != -1:
                if sequence[i] == self.upper_bound - 1:
                    return False
                sequence[i] += 1
                return True
        return False

    def next_row(self, sequence: list[int]) -> bool:
        """Adds a value to the sequence if possible.

        :param sequence: The sequence to be modified.
        :return: True if the operation is successful, false otherwise.
        """
        for i in range(len(sequence)):
            if sequence[i] == -1:
                sequence[i] = 0
                return True
        return False

    def prev_row(self, sequence: list[int]) -> bool:
        """Removes the last value of the sequence and advances the sequence if possible.

        :param sequence: The sequence to be modified.
        :return: True if the operation is successful, false otherwise.
        """
        for i in range(len(sequence) - 1, -1, -1):
            if sequence[i] != -1:
                sequence[i] = -1
                if self.advance(sequence):
                    return True
                else:
                    return self.prev_row(sequence)
        return False

    def next_sequence(self, sequence: list[int]) -> bool:
        """Finds the next candidate (partial) sequence if possible.

        :param sequence: The sequence to be modified.
        :return: True if the operation was successful, false otherwise.
        """
        if self.is_valid(sequence):
            return self.next_row(sequence) or self.advance(sequence) or self.prev_row(sequence)
        else:
            return self.advance(sequence) or self.prev_row(sequence)

    def next_valid_sequence(self, sequence: list[int]) -> bool:
        """Finds the next valid (partial) sequence if possible.

        :param sequence: The sequence to be modified.
        :return: True if the operation was successful, false otherwise.
        """
        while True:
            if not self.next_sequence(sequence):
                return False
            if self.is_valid(sequence):
                return True

    def generator(self, yield_partial: bool = False) -> typing.Generator[list[int], None, None]:
        """Creates a generator that generates valid sequences.

        :param yield_partial: Yield partial sequences. Defaults to false.
        :return: A generator.
        """
        sequence = [-1 for _ in range(self.length)]
        while self.next_valid_sequence(sequence):
            if yield_partial or self.is_complete(sequence):
                yield copy.deepcopy(sequence)


class SequenceOptimizer:
    """Determines the optimal sequence."""
    def __init__(
            self,
            seq_gen: typing.Iterable[list[int]],
            scoring_func: typing.Callable[[list[int]], float]
    ):
        """Constructs a SequenceOptimizer object.

        :param seq_gen: A sequence iterable.
        :param scoring_func: The function used to score sequences.
        """
        self.seq_gen = seq_gen
        self.scoring_func = scoring_func

    def generator(self) -> typing.Generator[list[int], None, None]:
        """Returns a generator that iteratively yields better sequences.

        :return: A generator object.
        """
        opt_score = -float('inf')
        for sequence in self.seq_gen:
            if (score := self.scoring_func(sequence)) > opt_score:
                opt_score = score
                yield copy.deepcopy(sequence)
