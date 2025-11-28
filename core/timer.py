"""Простой таймер для игры Сапёр.

Класс GameTimer не зависит от pygame и использует time.monotonic()
для отсчёта времени. Таймер поддерживает паузу и возобновление.
"""

from __future__ import annotations

import time
from typing import Optional


class GameTimer:
    """Таймер игры с поддержкой паузы.

    Таймер измеряет общее время в секундах, прошедшее между вызовами
    :meth:`start` и :meth:`stop` с учётом пауз. Внутри используется
    time.monotonic(), что делает измерения независимыми от изменения
    системных часов.
    """

    def __init__(self) -> None:
        """Создать новый остановленный таймер."""
        self._start_time: Optional[float] = None
        self._accumulated_time: float = 0.0
        self._running: bool = False

    def start(self) -> None:
        """Запустить таймер.

        Если таймер уже запущен, повторный вызов метода не изменяет
        его состояние.
        """
        if self._running:
            return
        self._start_time = time.monotonic()
        self._running = True

    def pause(self) -> None:
        """Приостановить таймер.

        Если таймер не запущен, метод ничего не делает.
        """
        if not self._running or self._start_time is None:
            return
        now = time.monotonic()
        self._accumulated_time += now - self._start_time
        self._start_time = None
        self._running = False

    def resume(self) -> None:
        """Возобновить работу таймера после паузы.

        Если таймер уже запущен, метод ничего не делает.
        """
        if self._running:
            return
        self._start_time = time.monotonic()
        self._running = True

    def reset(self) -> None:
        """Сбросить таймер в начальное состояние."""
        self._start_time = None
        self._accumulated_time = 0.0
        self._running = False

    def get_elapsed_seconds(self) -> int:
        """Получить общее прошедшее время в секундах.

        Returns:
            Целое число секунд, прошедших с момента запуска таймера
            с учётом пауз. Дробная часть отбрасывается.
        """
        total = self._accumulated_time
        if self._running and self._start_time is not None:
            now = time.monotonic()
            total += now - self._start_time
        return int(total)
