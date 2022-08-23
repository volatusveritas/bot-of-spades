from io import TextIOWrapper
from pathlib import Path
from json import dump, load
from typing import Optional
import os.path as path


class JSONFileWrapperReadOnly:
    def __init__(self, path: Path) -> None:
        self._file: Optional[TextIOWrapper] = None
        self._path: Path = path

    def _open_json(self) -> None:
        self._file = self._path.open("r")

    def _close_json(self) -> None:
        if self._file:
            self._file.close()

    def __enter__(self):
        if not self._path.exists():
            raise FileNotFoundError(self._path.name)

        self._open_json()

        return (
            load(self._file) if self._file and path.getsize(self._path) else {}
        )

    def __exit__(self, exc_type, exc_value, trace) -> bool:
        self._close_json()

        return False


class JSONFileWrapperUpdate(JSONFileWrapperReadOnly):
    def __init__(self, path: Path) -> None:
        super().__init__(path)

        self._dict: dict

    def _open_json(self) -> None:
        self._file = self._path.open("r+")

    def _close_json(self) -> None:
        if self._file:
            self._file.seek(0)
            self._file.truncate(0)
            dump(self._dict, self._file, indent=2)
            self._file.close()

    def __enter__(self):
        self._dict = super().__enter__()
        return self._dict
