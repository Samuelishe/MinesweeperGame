"""Управление одной игровой сессией Сапёра.

GameSession связывает воедино:
    * Board — состояние поля;
    * GameRules — правила;
    * GameTimer — время;
    * GameStatus и флаг паузы.

Модуль не зависит от pygame и может использоваться как в UI, так и в тестах.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.board import Board
from core.enums import GameStatus
from core.results import BoardUpdateResult
from core.settings import DEFAULT_SAFE_ZONE_RADIUS, DEFAULT_USE_QUESTION_MARKS
from core.timer import GameTimer
from game.rules import GameRules


@dataclass(slots=True)
class SessionSettings:
    """Настройки одной игровой сессии.

    Attributes:
        width:
            Ширина поля в клетках.
        height:
            Высота поля в клетках.
        mine_count:
            Количество мин.
        safe_zone_radius:
            Радиус безопасной зоны вокруг первой открытой клетки.
            0 — безопасна только клетка, по которой кликнули.
        use_question_marks:
            Определяет, используется ли цикл пометки с вопросительным знаком.
    """

    width: int
    height: int
    mine_count: int
    safe_zone_radius: int = DEFAULT_SAFE_ZONE_RADIUS
    use_question_marks: bool = DEFAULT_USE_QUESTION_MARKS


class GameSession:
    """Одна игровая сессия Сапёра.

    Экземпляр GameSession создаётся для конкретной конфигурации поля.
    Он управляет жизненным циклом партии: запуск, обработка ходов,
    пауза, завершение (победа/поражение).
    """

    def __init__(self, settings: SessionSettings, rules: GameRules) -> None:
        """Создать новую игровую сессию."""
        self._settings: SessionSettings = settings
        self._rules: GameRules = rules

        self._timer: GameTimer = GameTimer()
        self._board: Board = self._create_board(settings=settings)

        self._status: GameStatus = GameStatus.NOT_STARTED
        self._is_paused: bool = False

        # Счётчик оставшихся мин/флагов. Изначально равен числу мин.
        self._remaining_flags: int = settings.mine_count

    # --- Свойства ---

    @property
    def board(self) -> Board:
        """Текущее игровое поле."""
        return self._board

    @property
    def status(self) -> GameStatus:
        """Текущее состояние партии (NOT_STARTED, IN_PROGRESS, WON, LOST)."""
        return self._status

    @property
    def is_paused(self) -> bool:
        """Признак того, что игра находится на паузе."""
        return self._is_paused

    @property
    def timer(self) -> GameTimer:
        """Таймер текущей сессии."""
        return self._timer

    @property
    def timer_value(self) -> int:
        """Текущее игровое время в секундах (для HUD)."""
        return self.get_elapsed_seconds()

    @property
    def remaining_flags(self) -> int:
        """Количество флагов, доступных игроку.

        Это значение можно отображать в HUD как "оставшиеся мины".
        """
        return self._remaining_flags

    @property
    def settings(self) -> SessionSettings:
        """Настройки данной сессии."""
        return self._settings

    # --- Внутренние помощники ---

    @staticmethod
    def _create_board(settings: SessionSettings) -> Board:
        """Создать и инициализировать поле для игры."""
        return Board(
            width=settings.width,
            height=settings.height,
            mine_count=settings.mine_count,
            safe_zone_radius=settings.safe_zone_radius,
            use_question_marks=settings.use_question_marks,
        )

    def restart(self, *, keep_settings: bool = True) -> None:
        """Перезапустить игру."""
        if not keep_settings:
            # Логика изменения настроек может быть реализована на верхнем уровне.
            pass

        self._timer.reset()
        self._board = self._create_board(settings=self._settings)
        self._status = GameStatus.NOT_STARTED
        self._is_paused = False
        self._remaining_flags = self._settings.mine_count

    def set_settings(self, settings: SessionSettings) -> None:
        """Обновить настройки и перезапустить сессию."""
        self._settings = settings
        self.restart(keep_settings=True)

    def _ensure_can_play(self) -> bool:
        """Проверить, можно ли выполнять игровые действия."""
        if self._is_paused:
            return False
        if self._status in (GameStatus.WON, GameStatus.LOST):
            return False
        return True

    # --- Игровые действия ---

    def open_tile(self, x: int, y: int) -> Optional[BoardUpdateResult]:
        """Обработать попытку открыть клетку."""
        if not self._ensure_can_play():
            return None

        if self._status is GameStatus.NOT_STARTED:
            self._status = GameStatus.IN_PROGRESS
            self._timer.start()

        result = self._rules.open_tile(board=self._board, x=x, y=y)

        if result.exploded:
            self._status = GameStatus.LOST
            self._timer.pause()
        elif result.won:
            self._status = GameStatus.WON
            self._timer.pause()

        return result

    def toggle_flag(self, x: int, y: int) -> Optional[int]:
        """Переключить пометку клетки (флаг/вопрос/пусто).

        Возвращает:
            int | None: смещение количества выставленных флагов:
                +1 — флаг поставлен,
                -1 — флаг убран или заменён на вопрос,
                 0 — состояние не изменилось.
            None — если ход сейчас делать нельзя (пауза или игра закончена).
        """
        if not self._ensure_can_play():
            return None

        delta = self._rules.toggle_flag(board=self._board, x=x, y=y)

        if delta != 0:
            # remaining_flags хранит количество оставшихся флагов,
            # поэтому при постановке флага (delta=+1) уменьшаем значение,
            # а при снятии (delta=-1) увеличиваем.
            self._remaining_flags -= delta

            # На всякий случай ограничим диапазон.
            if self._remaining_flags < 0:
                self._remaining_flags = 0
            elif self._remaining_flags > self._settings.mine_count:
                self._remaining_flags = self._settings.mine_count

        return delta


    # Алиасы под API UI-слоя (events.py ожидает именно такие имена)

    def reveal_tile(self, x: int, y: int) -> Optional[BoardUpdateResult]:
        """Алиас для :meth:`open_tile`, используемый UI-слоем."""
        return self.open_tile(x=x, y=y)

    def cycle_tile_mark(self, x: int, y: int) -> Optional[int]:
        """Алиас для :meth:`toggle_flag`, используемый UI-слоем."""
        return self.toggle_flag(x=x, y=y)

    # --- Пауза и время ---

    def pause(self) -> None:
        """Поставить игру на паузу."""
        if self._is_paused:
            return
        if self._status is not GameStatus.IN_PROGRESS:
            return
        self._is_paused = True
        self._timer.pause()

    def resume(self) -> None:
        """Снять игру с паузы."""
        if not self._is_paused:
            return
        if self._status is not GameStatus.IN_PROGRESS:
            self._is_paused = False
            return
        self._is_paused = False
        self._timer.resume()

    def toggle_pause(self) -> None:
        """Переключить состояние паузы."""
        if self._is_paused:
            self.resume()
        else:
            self.pause()

    def get_elapsed_seconds(self) -> int:
        """Получить прошедшее игровое время в секундах."""
        return self._timer.get_elapsed_seconds()
