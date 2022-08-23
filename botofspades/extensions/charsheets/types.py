from typing import Any


class Field:
    def __init__(self, value: Any) -> None:
        self._value: Any = value

    def __str__(self) -> str:
        return str(self._value)

    @staticmethod
    def validate(value: Any) -> bool:
        return False

    def to_python_obj(self) -> Any:
        return self._value


class Abacus(Field):
    def __init__(self, value: Any) -> None:
        self._value: int = int(value)

    @staticmethod
    def validate(value: Any) -> bool:
        try:
            int(value)
        except:
            return False

        return True

    def to_python_obj(self) -> int:
        return self._value


class Rational(Field):
    def __init__(self, value: Any) -> None:
        self._value: float = float(value)

    @staticmethod
    def validate(value: Any) -> bool:
        try:
            float(value)
        except:
            return False

        return True

    def to_python_obj(self) -> float:
        return self._value


class Lever(Field):
    def __init__(self, value: Any) -> None:
        value = value.lower()

        if value in ("on", "true", "1", 1):
            self._value: bool = True
        elif value in ("off", "false", "0", 0):
            self._value: bool = False
        else:
            raise ValueError(f"Invalid value '{value}' for Lever field")

    def __str__(self) -> str:
        return "on" if self._value else "off"

    def to_python_obj(self) -> bool:
        return self._value


class Scroll(Field):
    def __init__(self, value: Any) -> None:
        self._value: str = str(value)

    def to_python_obj(self) -> str:
        return self._value


class Gauge(Field):
    def __init__(self, value: Any) -> None:
        if isinstance(value, (list, tuple)):
            self._current: int = int(value[0])
            self._max: int = int(value[1])
        elif isinstance(value, str):
            gauge_sides: list[str] = value.split("/")
            self._current: int = int(gauge_sides[0])
            self._max: int = int(gauge_sides[1])
        else:
            raise TypeError(
                "Gauge() argument must be a string or a Sequence[int, int],"
                f" not '{type(value)}'"
            )

    def __str__(self) -> str:
        return f"{self._current}/{self._max}"

    def to_python_obj(self) -> tuple[int, int]:
        return (self._current, self._max)
