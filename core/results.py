"""Структуры данных для описания изменений на поле после хода игрока."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(slots=True)
class BoardUpdateResult:
    """Результат одного действия на игровом поле.

    Attributes:
        changed:
            Список координат клеток (x, y), состояние которых было изменено.
            Координаты заданы в системе координат поля, где (0, 0) — верхний левый угол.
        exploded:
            True, если ход привёл к подрыву на мине.
        won:
            True, если после данного хода выполнены условия победы.
    """

    changed: List[Tuple[int, int]]
    exploded: bool
    won: bool
