"""Глобальные настройки логики Сапёра и пресеты уровней сложности.

Модуль не зависит от pygame и может использоваться как в игре, так и в тестах.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .enums import DifficultyLevel

# Ограничения размеров поля и количества мин.
# Эти константы используются для валидации конфигурации Board.
MIN_BOARD_WIDTH: int = 5
MIN_BOARD_HEIGHT: int = 5
MAX_BOARD_WIDTH: int = 50
MAX_BOARD_HEIGHT: int = 50

# Ограничения на количество мин: минимум 1 и максимум
# "все клетки кроме одной" (чтобы можно было выиграть).
MIN_MINES_COUNT: int = 1

#: Минимальное допустимое количество мин (алиас для совместимости с Board).
MIN_MINES: int = MIN_MINES_COUNT

#: Максимальная доля мин от общего числа клеток (0.0–1.0).
#: Используется для расчёта верхнего порога валидации.
MAX_MINES_FACTOR: float = 0.85

#: Радиус безопасной зоны вокруг первого клика по умолчанию.
#: 0 — безопасна только клетка клика; 1 — квадрат 3×3 и т.д.
DEFAULT_SAFE_ZONE_RADIUS: int = 1

#: Использовать ли вопросительные знаки по умолчанию.
DEFAULT_USE_QUESTION_MARKS: bool = True


@dataclass(slots=True)
class DifficultyConfig:
    """Описание пресета сложности.

    Attributes:
        width:
            Ширина поля в клетках.
        height:
            Высота поля в клетках.
        mine_count:
            Количество мин на поле.
    """

    width: int
    height: int
    mine_count: int


#: Пресеты классической сложности, соответствующие каноническому Сапёру.
DEFAULT_DIFFICULTIES: Dict[DifficultyLevel, DifficultyConfig] = {
    DifficultyLevel.BEGINNER: DifficultyConfig(width=9, height=9, mine_count=10),
    DifficultyLevel.INTERMEDIATE: DifficultyConfig(width=16, height=16, mine_count=40),
    DifficultyLevel.EXPERT: DifficultyConfig(width=30, height=16, mine_count=99),
}
