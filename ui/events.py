"""Обработка пользовательского ввода (мышь) для игры Сапёр.

Модуль предоставляет функции, которые:
    * преобразуют координаты мыши в координаты клетки;
    * вызывают соответствующие методы GameSession;
    * не содержат логики отрисовки.
"""

from __future__ import annotations

from typing import Optional, Tuple

import pygame

from core.board import Board
from core.results import BoardUpdateResult
from game.app_state import AppScreen, AppStateManager
from game.session import GameSession
from ui.renderer import LayoutInfo


Position = Tuple[int, int]


def handle_mouse_button_down(
    event: pygame.event.Event,
    app_state_manager: AppStateManager,
    session: Optional[GameSession],
    layout: Optional[LayoutInfo],
) -> Optional[BoardUpdateResult]:
    """Обработать нажатие кнопки мыши.

    Args:
        event:
            Событие pygame.MOUSEBUTTONDOWN.
        app_state_manager:
            Менеджер состояния приложения.
        session:
            Текущая игровая сессия (если есть).
        layout:
            Текущая разметка поля. Если None — клик вне игрового поля.

    Returns:
        BoardUpdateResult, если на поле произошло обновление,
        иначе None.
    """
    if session is None or layout is None:
        return None

    if app_state_manager.state.current_screen is not AppScreen.GAME:
        return None

    board = session.board

    mouse_pos: Position = event.pos
    tile_coords = _mouse_position_to_tile(
        position=mouse_pos,
        layout=layout,
        board=board,
    )
    if tile_coords is None:
        return None

    x, y = tile_coords

    if event.button == pygame.BUTTON_LEFT:
        return session.reveal_tile(x, y)
    if event.button == pygame.BUTTON_RIGHT:
        return session.cycle_tile_mark(x, y)

    return None


def _mouse_position_to_tile(
    position: Position,
    layout: LayoutInfo,
    board: Board,
) -> Optional[Tuple[int, int]]:
    """Преобразовать координаты мыши в координаты клетки.

    Args:
        position:
            Позиция мыши в пикселях (x, y).
        layout:
            Параметры разметки (origin и размер тайла).
        board:
            Игровое поле.

    Returns:
        Пара (x, y) — координаты клетки в системе Board,
        либо None, если клик пришёлся вне поля.
    """
    mouse_x, mouse_y = position

    origin_x: int = layout.origin_x
    origin_y: int = layout.origin_y
    tile_size: int = layout.tile_size

    if (
        mouse_x < origin_x
        or mouse_y < origin_y
        or mouse_x >= origin_x + board.width * tile_size
        or mouse_y >= origin_y + board.height * tile_size
    ):
        return None

    tile_x: int = (mouse_x - origin_x) // tile_size
    tile_y: int = (mouse_y - origin_y) // tile_size

    if tile_x < 0 or tile_x >= board.width:
        return None
    if tile_y < 0 or tile_y >= board.height:
        return None

    return tile_x, tile_y
