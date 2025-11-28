"""Перечисления, используемые логикой игры Сапёр.

Здесь собраны базовые enum-классы, которые описывают состояние клеток,
состояние игры и уровни сложности. Модуль не зависит от pygame.
"""

from __future__ import annotations

from enum import Enum, auto


class TileState(Enum):
    """Состояние клетки игрового поля.

    Attributes:
        HIDDEN: Клетка закрыта.
        REVEALED: Клетка открыта.
        FLAGGED: Клетка помечена флагом.
        QUESTION: Клетка помечена вопросительным знаком.
    """

    HIDDEN = auto()
    REVEALED = auto()
    FLAGGED = auto()
    QUESTION = auto()


class TileContent(Enum):
    """Тип содержимого клетки.

    Attributes:
        EMPTY: Пустая клетка (0 соседних мин).
        NUMBER: Клетка с числом (1–8 соседних мин).
        MINE: Клетка с миной.
        SPECIAL: Особое содержимое (ловушки, бонусы и т.п.).
    """

    EMPTY = auto()
    NUMBER = auto()
    MINE = auto()
    SPECIAL = auto()


class GameStatus(Enum):
    """Состояние партии.

    Attributes:
        NOT_STARTED: Игра ещё не начата (нет первого клика).
        IN_PROGRESS: Игра идёт.
        WON: Игрок победил.
        LOST: Игрок подорвался на мине.
    """

    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    WON = auto()
    LOST = auto()


class DifficultyLevel(Enum):
    """Уровни сложности классического режима.

    Attributes:
        BEGINNER: Новичок.
        INTERMEDIATE: Средний уровень.
        EXPERT: Эксперт.
        CUSTOM: Пользовательские настройки поля.
    """

    BEGINNER = auto()
    INTERMEDIATE = auto()
    EXPERT = auto()
    CUSTOM = auto()
