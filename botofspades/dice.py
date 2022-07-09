from __future__ import annotations

import random

from botofspades import unicode


def roll(lower_limit:int, upper_limit:int) -> int:
    return random.randint(lower_limit, upper_limit)


class Dice:
    def __init__(self, lower_limit:int, upper_limit:int, amount:int=1) -> None:
        self.lower_limit: int = lower_limit
        self.upper_limit: int = upper_limit
        self.amount: int = amount

    def __mul__(self, other:int) -> Dice:
        return Dice(self.lower_limit, self.upper_limit, self.amount * other)

    def roll(self) -> DiceResult:
        return DiceResult([
            roll(self.lower_limit, self.upper_limit)
            for _ in range(self.amount)
        ])

    def rollmany(self, amount:int) -> DiceResult:
        final_result: DiceResult = DiceResult()

        for _ in range(amount):
            final_result += self.roll()

        return final_result


class DicePool:
    def __init__(self, dice:Dice, *more_dice:Dice) -> None:
        self.dice: list[Dice] = [dice]
        self.dice.extend(more_dice)

    def add_dice(self, dice:Dice, *more_dice:Dice) -> None:
        self.dice.append(dice)
        self.dice.extend(more_dice)

    def remove_dice(self, index:int, *indexes:int) -> None:
        self.dice.pop(index)
        for index in indexes:
            self.dice.pop(index)

    def roll(self) -> DiceResult:
        final_result: DiceResult = DiceResult()

        for dice in self.dice:
            final_result += dice.roll()

        return final_result

    def rollmany(self, amount:int) -> DiceResult:
        final_result: DiceResult = DiceResult()

        for _ in range(amount):
            final_result += self.roll()

        return final_result


class DiceResult:
    def __init__(self, results:list[int]=[]) -> None:
        self.results: list[int] = results
        self.total: int = sum(results)

    def __int__(self) -> int:
        return self.total

    def __add__(self, other: DiceResult) -> DiceResult:
        result: DiceResult = DiceResult()
        result.results = self.results + other.results
        result.total = self.total + other.total

        return result


D4 = Dice(1, 4)
D6 = Dice(1, 6)
D8 = Dice(1, 8)
D10 = Dice(1, 10)
D12 = Dice(1, 12)
D20 = Dice(1, 20)
D100 = Dice(1, 100)
