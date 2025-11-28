"""Отрисовка игры Сапёр с поддержкой автомасштаба.

Модуль содержит класс BoardRenderer, который:
    * вычисляет размеры тайлов и отступы в зависимости от размера окна;
    * рисует поле и HUD (таймер, счётчик мин);
    * не содержит игровой логики — только чтение состояния из GameSession.

Рендерер не управляет главным циклом, фуллскрином и обработкой событий.
Это ответственность верхнего уровня (ui.main_window и ui.events).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import pygame

from core.board import Board
from core.enums import GameStatus, TileState
from game.session import GameSession
from ui.themes import Color, Theme

# Пути к шрифтам (ожидается, что файлы лежат в assets/fonts).
UI_FONT_PATH: str = "assets/fonts/Inter-VariableFont_opsz,wght.ttf"

@dataclass(slots=True)
class LayoutInfo:
    """Параметры текущей разметки поля и HUD.

    Attributes:
        hud_rect:
            Прямоугольник HUD (панели с таймером и счётчиком мин).
        board_rect:
            Прямоугольник области отрисовки поля.
        tile_size:
            Размер тайла в пикселях (квадрат).
        origin_x:
            X-координата левого верхнего угла поля.
        origin_y:
            Y-координата левого верхнего угла поля.
    """

    hud_rect: pygame.Rect
    board_rect: pygame.Rect
    tile_size: int
    origin_x: int
    origin_y: int


# Константы для разметки и отступов.
HUD_HEIGHT_FRACTION: float = 0.12
BOARD_MARGIN_FRACTION: float = 0.08
MIN_TILE_SIZE: int = 12
MAX_TILE_SIZE: int = 64
GRID_LINE_WIDTH: int = 1


class BoardRenderer:
    """Рендерер игрового поля и HUD.

    Экземпляр не знает про pygame.display.set_mode и не хранит ссылку
    на окно. Вместо этого окно при каждом кадре передаётся в draw().
    """

    def __init__(self, theme: Theme) -> None:
        """Создать рендерер.

        Args:
            theme:
                Тема оформления.
        """
        self._theme: Theme = theme
        # Кеш шрифтов по размеру, чтобы не дергать диск на каждый тайл.
        self._ui_font_cache: Dict[int, pygame.font.Font] = {}
        self._emoji_font_cache: Dict[int, pygame.font.Font] = {}

    @staticmethod
    def calculate_min_window_size(board: Board) -> Tuple[int, int]:
        """Рассчитать минимальный разумный размер окна для данного поля.

        Здесь мы исходим из минимального размера тайла и минимального
        размера HUD, чтобы всё было читаемо.

        Args:
            board:
                Игровое поле.

        Returns:
            Пару (width, height) в пикселях.
        """
        min_tile_size: int = MIN_TILE_SIZE

        hud_height: int = int(min_tile_size * board.height * HUD_HEIGHT_FRACTION)
        if hud_height < min_tile_size * 2:
            hud_height = min_tile_size * 2

        logical_board_height: int = board.height * min_tile_size
        board_margin: int = int(logical_board_height * BOARD_MARGIN_FRACTION)

        width: int = board.width * min_tile_size + 2 * board_margin
        height: int = hud_height + logical_board_height + 2 * board_margin

        return width, height

    @staticmethod
    def calculate_layout(surface: pygame.Surface, board: Board) -> LayoutInfo:
        """Посчитать разметку HUD и поля под текущий размер окна.

        Args:
            surface:
                Поверхность окна.
            board:
                Игровое поле.

        Returns:
            Объект LayoutInfo с параметрами размещения.
        """
        window_width, window_height = surface.get_size()

        hud_height: int = int(window_height * HUD_HEIGHT_FRACTION)
        if hud_height < MIN_TILE_SIZE * 2:
            hud_height = MIN_TILE_SIZE * 2

        board_height_available: int = window_height - hud_height
        board_margin: int = int(board_height_available * BOARD_MARGIN_FRACTION)

        max_board_width: int = window_width - 2 * board_margin
        max_board_height: int = board_height_available - 2 * board_margin

        tile_size_by_width: int = max_board_width // board.width
        tile_size_by_height: int = max_board_height // board.height
        tile_size: int = min(tile_size_by_width, tile_size_by_height)

        tile_size = max(MIN_TILE_SIZE, min(tile_size, MAX_TILE_SIZE))

        board_pixel_width: int = tile_size * board.width
        board_pixel_height: int = tile_size * board.height

        origin_x: int = (window_width - board_pixel_width) // 2
        origin_y: int = hud_height + (board_height_available - board_pixel_height) // 2

        hud_rect = pygame.Rect(0, 0, window_width, hud_height)
        board_rect = pygame.Rect(origin_x, origin_y, board_pixel_width, board_pixel_height)

        return LayoutInfo(
            hud_rect=hud_rect,
            board_rect=board_rect,
            tile_size=tile_size,
            origin_x=origin_x,
            origin_y=origin_y,
        )

    def draw(self, surface: pygame.Surface, session: GameSession) -> None:
        """Отрисовать полный кадр игры (фон, HUD, поле).

        Args:
            surface:
                Поверхность окна.
            session:
                Текущая игровая сессия.
        """
        layout = self.calculate_layout(surface=surface, board=session.board)

        self._draw_background(surface)
        self._draw_hud(surface=surface, session=session, layout=layout)
        self._draw_board(surface=surface, session=session, layout=layout)

    # === Работа со шрифтами ==================================================

    def _get_ui_font(self, size: int) -> pygame.font.Font:
        """Получить UI-шрифт Inter нужного размера.

        При отсутствии файла шрифта использует системный шрифт Consolas.
        """
        size = max(8, size)
        cached = self._ui_font_cache.get(size)
        if cached is not None:
            return cached

        try:
            font = pygame.font.Font(UI_FONT_PATH, size)
        except (FileNotFoundError, OSError):
            font = pygame.font.SysFont("consolas", size)

        self._ui_font_cache[size] = font
        return font

    def _get_emoji_font(self, size: int) -> pygame.font.Font:
        """Получить emoji-шрифт нужного размера.

        Шаги:
        1) Пробуем системный 'Segoe UI Emoji'.
        2) Проверяем пробным рендером, что шрифт реально работает.
        3) Если не работает — откат на UI-шрифт Inter.
        """
        size = max(8, size)

        cached = self._emoji_font_cache.get(size)
        if cached is not None:
            return cached

        # Пытаемся получить системный шрифт
        try:
            font = pygame.font.SysFont("Segoe UI Emoji", size)
        except (OSError, FileNotFoundError):
            font = self._get_ui_font(size)
        else:
            # Проверочный рендер
            try:
                probe = font.render("🙂", True, (0, 0, 0))
                if probe.get_width() == 0:
                    font = self._get_ui_font(size)
            except pygame.error:
                font = self._get_ui_font(size)

        self._emoji_font_cache[size] = font
        return font



    # === Отрисовка ===========================================================

    def _draw_background(self, surface: pygame.Surface) -> None:
        """Отрисовать фоновый цвет окна."""
        surface.fill(self._theme.background_color)

    def _draw_hud(
        self,
        surface: pygame.Surface,
        session: GameSession,
        layout: LayoutInfo,
    ) -> None:
        """Отрисовать HUD (таймер, счётчик мин, статус)."""
        width, _ = surface.get_size()
        hud_rect = pygame.Rect(
            0,
            0,
            width,
            layout.hud_rect.height,
        )

        pygame.draw.rect(surface, self._theme.hud_background_color, hud_rect)

        timer_text: str = f"{session.timer_value:03}"
        mines_text: str = f"{session.remaining_flags:03}"

        hud_height: int = hud_rect.height
        ui_font_size: int = max(16, int(hud_height * 0.6))
        emoji_font_size: int = max(20, int(hud_height * 0.8))

        ui_font = self._get_ui_font(ui_font_size)
        emoji_font = self._get_emoji_font(emoji_font_size)

        # Таймер слева
        timer_surface = ui_font.render(timer_text, True, self._theme.hud_text_color)
        timer_rect = timer_surface.get_rect(left=16, centery=hud_rect.centery)
        surface.blit(timer_surface, timer_rect)

        # Счётчик мин справа
        mines_surface = ui_font.render(mines_text, True, self._theme.hud_text_color)
        mines_rect = mines_surface.get_rect(right=width - 16, centery=hud_rect.centery)
        surface.blit(mines_surface, mines_rect)

        # Эмодзи-статус по центру
        if session.status is GameStatus.IN_PROGRESS:
            status_text: str = "🙂"
        elif session.status is GameStatus.WON:
            status_text = "😎"
        elif session.status is GameStatus.LOST:
            status_text = "😵"
        else:
            # На старте и в потенциальной паузе показываем нейтральный смайл
            status_text = "🙂"

        # Пытаемся рисовать цветным emoji-шрифтом, при ошибке — откат на UI-шрифт
        try:
            status_surface = emoji_font.render(
                status_text,
                True,
                self._theme.hud_text_color,
            )
        except pygame.error:
            status_surface = ui_font.render(
                status_text,
                True,
                self._theme.hud_text_color,
            )

        status_rect = status_surface.get_rect(center=hud_rect.center)
        surface.blit(status_surface, status_rect)


    def _draw_board(
        self,
        surface: pygame.Surface,
        session: GameSession,
        layout: LayoutInfo,
    ) -> None:
        """Отрисовать поле."""
        board = session.board
        tile_size: int = layout.tile_size

        pygame.draw.rect(
            surface,
            self._theme.board_background_color,
            layout.board_rect,
        )

        for y in range(board.height):
            for x in range(board.width):
                tile_state = board.get_tile_state(x, y)
                is_mine = board.is_mine(x, y)
                adjacent_mines = board.get_adjacent_mines(x, y)

                tile_rect = pygame.Rect(
                    layout.origin_x + x * tile_size,
                    layout.origin_y + y * tile_size,
                    tile_size,
                    tile_size,
                )

                self._draw_tile(
                    surface=surface,
                    rect=tile_rect,
                    state=tile_state,
                    is_mine=is_mine,
                    adjacent_mines=adjacent_mines,
                )

        self._draw_grid(surface=surface, layout=layout, board=board)

    def _draw_grid(
        self,
        surface: pygame.Surface,
        layout: LayoutInfo,
        board: Board,
    ) -> None:
        """Отрисовать сетку поверх поля."""
        tile_size: int = layout.tile_size
        origin_x: int = layout.origin_x
        origin_y: int = layout.origin_y

        color: Color = self._theme.tile_border_color

        for x in range(board.width + 1):
            x_pos: int = origin_x + x * tile_size
            pygame.draw.line(
                surface,
                color,
                (x_pos, origin_y),
                (x_pos, origin_y + board.height * tile_size),
                GRID_LINE_WIDTH,
            )

        for y in range(board.height + 1):
            y_pos: int = origin_y + y * tile_size
            pygame.draw.line(
                surface,
                color,
                (origin_x, y_pos),
                (origin_x + board.width * tile_size, y_pos),
                GRID_LINE_WIDTH,
            )

    def _draw_tile(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        state: TileState,
        is_mine: bool,
        adjacent_mines: int,
    ) -> None:
        """Отрисовать одну клетку."""
        if state is TileState.REVEALED:
            pygame.draw.rect(surface, self._theme.tile_revealed_color, rect)
        else:
            pygame.draw.rect(surface, self._theme.tile_hidden_color, rect)

        pygame.draw.rect(
            surface,
            self._theme.tile_border_color,
            rect,
            GRID_LINE_WIDTH,
        )

        if state is TileState.FLAGGED:
            self._draw_flag(surface=surface, rect=rect)
            return

        if state is TileState.QUESTION:
            self._draw_question_mark(surface=surface, rect=rect)
            return

        if state is TileState.REVEALED:
            if is_mine:
                self._draw_mine(surface=surface, rect=rect)
            elif adjacent_mines > 0:
                self._draw_number(
                    surface=surface,
                    rect=rect,
                    value=adjacent_mines,
                )

    def _draw_mine(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Отрисовать мину в клетке."""
        center = rect.center
        radius: int = rect.width // 3
        pygame.draw.circle(surface, self._theme.mine_color, center, radius)

    def _draw_flag(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Отрисовать флаг в клетке."""
        pole_x: int = rect.left + rect.width // 3
        pole_y_top: int = rect.top + rect.height // 5
        pole_y_bottom: int = rect.bottom - rect.height // 5

        pygame.draw.line(
            surface,
            self._theme.flag_color,
            (pole_x, pole_y_top),
            (pole_x, pole_y_bottom),
            2,
        )

        flag_points = [
            (pole_x, pole_y_top),
            (pole_x + rect.width // 2, pole_y_top + rect.height // 4),
            (pole_x, pole_y_top + rect.height // 2),
        ]
        pygame.draw.polygon(surface, self._theme.flag_color, flag_points)

    def _draw_number(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        value: int,
    ) -> None:
        """Отрисовать число соседних мин."""
        font_size: int = max(12, rect.height - 4)
        font = self._get_ui_font(font_size)

        color: Color = self._theme.get_number_color(value)
        text: str = str(value)

        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

    def _draw_question_mark(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Отрисовать знак вопроса в клетке."""
        font_size: int = max(12, rect.height - 4)
        font = self._get_ui_font(font_size)

        text_surface = font.render("?", True, self._theme.hud_text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)
