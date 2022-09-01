from typing import Any
from math import ceil, floor


# Any value coming from Discord is a string.
# Values in a character sheet may be any JSON value.
# They are otherwise Python values.

# Type name > Discord (string) | JSON | Python
# --------------------------------------------
# Abacus > "x" | number("x") | int("x")
# Rational > "x.y" | number("x.y") | float("x.y")
# Lever > "on"/"true"/"1"/"off"/"false"/"0" | boolean | bool
# Scroll > "x" | "x" | "x"
# Gauge > "x/y" | array[number("x"), number("y")] | list[int("x"), int("y")]


Args = tuple[str, ...]


class Field:
    @staticmethod
    def validate(value: Any) -> bool:
        """Validates a Python value."""
        return False

    @staticmethod
    def from_str(value_str: str) -> Any:
        """Turns a string into a Python value. Expects a valid string."""
        return value_str

    @staticmethod
    def to_str(value: Any) -> str:
        """Turns a Python value into a string. Expects a valid value."""
        return str(value)


class Abacus(Field):
    @staticmethod
    def validate(value: Any) -> bool:
        try:
            int(value)
        except:
            return False

        return True

    @staticmethod
    def from_str(value_str: str) -> int:
        return int(value_str)

    @staticmethod
    def to_str(value: int) -> str:
        return str(value)

    # Type Methods receive the original value, and a list of args passed as a
    # string. If the type of an arg is invalid, it must raise TypeError.
    # Possible command for this: cs sh do <sheet> <field> <method> <args>*

    @staticmethod
    def method_add(value: int, args: Args) -> int:
        to_add: int

        try:
            to_add = int(args[0])
        except:
            raise TypeError

        return value + to_add

    @staticmethod
    def method_subtract(value: int, args: Args) -> int:
        to_sub: int

        try:
            to_sub = int(args[0])
        except:
            raise TypeError

        return value - to_sub

    @staticmethod
    def method_multiply(value: int, args: Args) -> int:
        to_mul: int

        try:
            to_mul = int(args[0])
        except:
            raise TypeError

        return value * to_mul

    @staticmethod
    def method_divide(value: int, args: Args) -> int:
        to_div: int

        try:
            to_div = int(args[0])
        except:
            raise TypeError

        return value // to_div


class Rational(Field):
    @staticmethod
    def validate(value: Any) -> bool:
        try:
            float(value)
        except:
            return False

        return True

    @staticmethod
    def from_str(value_str: str) -> float:
        return float(value_str)

    @staticmethod
    def to_str(value: float) -> str:
        return str(value)

    @staticmethod
    def method_add(value: float, args: Args) -> float:
        to_add: float

        try:
            to_add = float(args[0])
        except:
            raise TypeError

        return value + to_add

    @staticmethod
    def method_subtract(value: float, args: Args) -> float:
        to_sub: float

        try:
            to_sub = float(args[0])
        except:
            raise TypeError

        return value - to_sub

    @staticmethod
    def method_multiply(value: float, args: Args) -> float:
        to_mul: float

        try:
            to_mul = float(args[0])
        except:
            raise TypeError

        return value * to_mul

    @staticmethod
    def method_divide(value: float, args: Args) -> float:
        to_div: float

        try:
            to_div = float(args[0])
        except:
            raise TypeError

        return value / to_div

    @staticmethod
    def method_roundup(value: float, args: Args) -> float:
        return ceil(value)

    @staticmethod
    def method_rounddown(value: float, args: Args) -> float:
        return floor(value)

    @staticmethod
    def method_round(value: float, args: Args) -> float:
        # HACK: Manual float correction so a value of exactly 0.5 rounds down.
        return floor(value + 0.5 - 1e-16)


class Lever(Field):
    @staticmethod
    def validate(value: Any) -> bool:
        if not isinstance(value, str):
            try:
                bool(value)
            except:
                return False

            return True

        return value in (
            "on",
            "true",
            "1",
            "off",
            "false",
            "0",
        )

    @staticmethod
    def from_str(value_str: str) -> bool:
        return value_str in ("on", "true", "1")

    @staticmethod
    def to_str(value: bool) -> str:
        return "on" if value else "off"

    @staticmethod
    def method_toggle(value: bool, args: Args) -> bool:
        return not value


class Scroll(Field):
    @staticmethod
    def validate(value: Any) -> bool:
        try:
            str(value)
        except:
            return False

        return True

    @staticmethod
    def from_str(value_str: str) -> str:
        return value_str

    @staticmethod
    def to_str(value: str) -> str:
        return value


class Gauge(Field):
    @staticmethod
    def validate(value: Any) -> bool:
        if not isinstance(value, str):
            return (
                isinstance(value, (list, tuple))
                and len(value) >= 2
                and isinstance(value[0], int)
                and isinstance(value[1], int)
            )

        try:
            Gauge.from_str(value)
        except:
            return False

        return True

    @staticmethod
    def from_str(value_str: str) -> list[int]:
        return [int(section) for section in value_str.split("/")]

    @staticmethod
    def to_str(value: list[int] | tuple[int, int]) -> str:
        return f"{value[0]}/{value[1]}"

    @staticmethod
    def method_add(value: list[int], args: Args) -> list[int]:
        to_add: int

        try:
            to_add = int(args[0])
        except:
            raise TypeError

        return [value[0] + to_add, value[1]]

    @staticmethod
    def method_subtract(value: list[int], args: Args) -> list[int]:
        to_sub: int

        try:
            to_sub = int(args[0])
        except:
            raise TypeError

        return [value[0] - to_sub, value[1]]

    @staticmethod
    def method_increase(value: list[int], args: Args) -> list[int]:
        to_add: int

        try:
            to_add = int(args[0])
        except:
            raise TypeError

        return [value[0], value[1] + to_add]

    @staticmethod
    def method_decrease(value: list[int], args: Args) -> list[int]:
        to_sub: int

        try:
            to_sub = int(args[0])
        except:
            raise TypeError

        return [value[0], value[1] - to_sub]
