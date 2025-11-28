"""Application state and simple state machine for the Minesweeper game."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from core.enums import DifficultyLevel, GameStatus
from game.rules import GameRules
from game.session import GameSession, SessionSettings


class AppScreen(Enum):
    """Экраны приложения.

    Attributes:
        MAIN_MENU: Главное меню.
        GAME: Игровой экран.
        PAUSE_MENU: Меню паузы поверх игры.
        SETTINGS: Экран настроек (пока заглушка).
        CAMPAIGN_MENU: Меню кампании (пока заглушка).
        GAME_OVER: Экран результата игры (победа/поражение).
    """

    MAIN_MENU = auto()
    GAME = auto()
    PAUSE_MENU = auto()
    SETTINGS = auto()
    CAMPAIGN_MENU = auto()
    GAME_OVER = auto()


@dataclass(slots=True)
class AppState:
    """Текущее состояние приложения.

    Attributes:
        current_screen:
            Какой экран сейчас отображается.
        session:
            Текущая игровая сессия или None, если игры нет.
        session_settings:
            Последние использованные настройки игры.
        last_rules:
            Последняя использованная реализация правил (для рестарта).
    """

    current_screen: AppScreen = AppScreen.MAIN_MENU
    session: Optional[GameSession] = None
    session_settings: SessionSettings = field(
        default_factory=lambda: SessionSettings(width=9, height=9, mine_count=10),
    )
    last_rules: Optional[GameRules] = None


class AppStateManager:
    """Небольшая обёртка над AppState с удобными методами переходов."""

    def __init__(self) -> None:
        self._state: AppState = AppState()

    @property
    def state(self) -> AppState:
        """Вернуть текущее состояние приложения."""
        return self._state

    # === Экраны верхнего уровня ===

    def go_to_main_menu(self) -> None:
        """Показать главное меню, не сбрасывая сессию."""
        self._state.current_screen = AppScreen.MAIN_MENU

    def abort_to_main_menu(self) -> None:
        """Выйти в главное меню и сбросить текущую игру."""
        self._state.session = None
        self._state.current_screen = AppScreen.MAIN_MENU

    def show_settings(self) -> None:
        """Показать экран настроек (пока заглушка)."""
        self._state.current_screen = AppScreen.SETTINGS

    def show_campaign_menu(self) -> None:
        """Показать меню кампании (пока заглушка)."""
        self._state.current_screen = AppScreen.CAMPAIGN_MENU

    # === Управление игрой ===

    def start_game(self, settings: SessionSettings, rules: GameRules) -> None:
        """Создать новую игру и перейти на экран игры."""
        self._state.session_settings = settings
        self._state.last_rules = rules
        self._state.session = GameSession(settings=settings, rules=rules)
        self._state.current_screen = AppScreen.GAME

    def restart_game(self) -> None:
        """Перезапустить игру с теми же настройками и правилами."""
        if self._state.session_settings is None or self._state.last_rules is None:
            return

        self._state.session = GameSession(
            settings=self._state.session_settings,
            rules=self._state.last_rules,
        )
        self._state.current_screen = AppScreen.GAME

    def pause_game(self) -> None:
        """Поставить игру на паузу, если она идёт."""
        session = self._state.session
        if session is None:
            return
        if session.status is not GameStatus.IN_PROGRESS:
            return

        session.pause()
        self._state.current_screen = AppScreen.PAUSE_MENU

    def resume_game(self) -> None:
        """Продолжить игру из паузы."""
        session = self._state.session
        if session is None:
            return

        if session.status is GameStatus.IN_PROGRESS:
            session.resume()

        self._state.current_screen = AppScreen.GAME

    def show_game_over(self) -> None:
        """Показать экран результата игры поверх завершённой сессии."""
        session = self._state.session
        if session is None:
            return

        if session.status not in (GameStatus.WON, GameStatus.LOST):
            return

        self._state.current_screen = AppScreen.GAME_OVER
