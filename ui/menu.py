"""Simple menu views for the Minesweeper game."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import pygame

from ui.themes import Theme

# Константы оформления меню (без магических чисел в коде ниже)
MENU_CORNER_RADIUS: int = 8
MENU_WIDTH_RATIO: float = 0.5
MENU_PADDING_X: int = 32
MENU_PADDING_Y: int = 24
MENU_TITLE_FONT_SIZE: int = 32
MENU_SUBTITLE_FONT_SIZE: int = 22
MENU_ITEM_FONT_SIZE: int = 26
MENU_TITLE_MARGIN_BOTTOM: int = 16
MENU_SUBTITLE_MARGIN_BOTTOM: int = 12
MENU_ITEM_VERTICAL_SPACING: int = 8
MENU_ITEM_HEIGHT: int = 40
MENU_SHADOW_OFFSET: int = 6


@dataclass(slots=True)
class MenuItem:
    """Один пункт меню.

    Attributes:
        label: Надпись, отображаемая пользователю.
        action_id: Строковый идентификатор действия, который вернётся наружу.
    """

    label: str
    action_id: str


class BaseMenuView:
    """Базовый класс для простых вертикальных меню."""

    def __init__(
        self,
        title: str,
        items: Sequence[MenuItem],
        theme: Theme,
        subtitle_lines: Optional[Sequence[str]] = None,
    ) -> None:
        """Создать базовое меню."""
        self._title: str = title
        self._items: List[MenuItem] = list(items)
        self._theme: Theme = theme
        self._subtitle_lines: List[str] = list(subtitle_lines or [])
        self._selected_index: int = 0

        pygame.font.init()
        self._title_font: pygame.font.Font = pygame.font.Font(
            None,
            MENU_TITLE_FONT_SIZE,
        )
        self._subtitle_font: pygame.font.Font = pygame.font.Font(
            None,
            MENU_SUBTITLE_FONT_SIZE,
        )
        self._item_font: pygame.font.Font = pygame.font.Font(
            None,
            MENU_ITEM_FONT_SIZE,
        )

    # --- Публичное API ---

    def set_title(self, title: str) -> None:
        """Обновить заголовок меню."""
        self._title = title

    def set_subtitle_lines(self, subtitle_lines: Sequence[str]) -> None:
        """Обновить строки под заголовком (например, текст результатов)."""
        self._subtitle_lines = list(subtitle_lines)

    def reset_selection(self) -> None:
        """Сбросить выбор пункта меню к первому элементу."""
        if self._items:
            self._selected_index = 0

    def handle_key(self, key: int) -> Optional[str]:
        """Обработать нажатие клавиши (стрелки и Enter/Space)."""
        if not self._items:
            return None

        if key in (pygame.K_UP, pygame.K_w):
            self._selected_index = (self._selected_index - 1) % len(self._items)
            return None

        if key in (pygame.K_DOWN, pygame.K_s):
            self._selected_index = (self._selected_index + 1) % len(self._items)
            return None

        if key in (pygame.K_RETURN, pygame.K_SPACE):
            return self._items[self._selected_index].action_id

        return None

    # Удобные методы для GameApp:

    def move_selection_up(self) -> None:
        """Сдвинуть выбор вверх на один пункт."""
        self.handle_key(pygame.K_UP)

    def move_selection_down(self) -> None:
        """Сдвинуть выбор вниз на один пункт."""
        self.handle_key(pygame.K_DOWN)

    def confirm_selection(self) -> Optional[str]:
        """Подтвердить выбор текущего пункта (аналог Enter)."""
        return self.handle_key(pygame.K_RETURN)

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовать меню на переданной поверхности."""
        width, height = surface.get_size()

        # --- заранее рендерим заголовок и подзаголовки, чтобы знать их высоту ---

        title_surface = self._title_font.render(
            self._title,
            True,
            self._theme.menu_text_color,
        )
        title_height: int = title_surface.get_height()

        subtitle_surfaces: List[pygame.Surface] = []
        subtitle_heights_sum: int = 0
        for line in self._subtitle_lines:
            s_surf = self._subtitle_font.render(
                line,
                True,
                self._theme.menu_text_color,
            )
            subtitle_surfaces.append(s_surf)
            subtitle_heights_sum += s_surf.get_height()

        subtitle_count: int = len(subtitle_surfaces)

        # Высота блока с пунктами меню.
        items_count: int = len(self._items)
        if items_count > 0:
            items_block_height: int = (
                items_count * MENU_ITEM_HEIGHT
                + (items_count - 1) * MENU_ITEM_VERTICAL_SPACING
            )
        else:
            items_block_height = 0

        # Расчёт требуемой высоты меню.
        needed_height: int = 2 * MENU_PADDING_Y
        needed_height += title_height

        if subtitle_count > 0:
            needed_height += MENU_TITLE_MARGIN_BOTTOM
            needed_height += subtitle_heights_sum
            needed_height += (subtitle_count - 1) * MENU_SUBTITLE_MARGIN_BOTTOM

        if items_block_height > 0:
            # Добавляем небольшой зазор от последней подписи до списка пунктов.
            if subtitle_count == 0:
                needed_height += MENU_TITLE_MARGIN_BOTTOM
            needed_height += items_block_height

        # Не даём меню вылезти за экран вверх/вниз.
        max_menu_height: int = height - 2 * MENU_PADDING_Y
        menu_height: int = min(needed_height, max_menu_height)
        menu_width: int = int(width * MENU_WIDTH_RATIO)

        menu_rect = pygame.Rect(0, 0, menu_width, menu_height)
        menu_rect.center = surface.get_rect().center

        # Тень
        shadow_rect = menu_rect.copy()
        shadow_rect.x += MENU_SHADOW_OFFSET
        shadow_rect.y += MENU_SHADOW_OFFSET

        pygame.draw.rect(
            surface,
            self._theme.menu_shadow_color,
            shadow_rect,
            border_radius=MENU_CORNER_RADIUS,
        )

        # Основной прямоугольник меню
        pygame.draw.rect(
            surface,
            self._theme.menu_background_color,
            menu_rect,
            border_radius=MENU_CORNER_RADIUS,
        )
        pygame.draw.rect(
            surface,
            self._theme.menu_border_color,
            menu_rect,
            width=1,
            border_radius=MENU_CORNER_RADIUS,
        )

        # Внутренние отступы
        content_rect = menu_rect.inflate(-2 * MENU_PADDING_X, -2 * MENU_PADDING_Y)

        # Заголовок
        title_rect = title_surface.get_rect()
        title_rect.midtop = (content_rect.centerx, content_rect.top)
        surface.blit(title_surface, title_rect)

        y_cursor: int = title_rect.bottom + MENU_TITLE_MARGIN_BOTTOM

        # Подзаголовки (например, статус, время и т.д.)
        for s_surf in subtitle_surfaces:
            subtitle_rect = s_surf.get_rect()
            subtitle_rect.midtop = (content_rect.centerx, y_cursor)
            surface.blit(s_surf, subtitle_rect)
            y_cursor = subtitle_rect.bottom + MENU_SUBTITLE_MARGIN_BOTTOM

        # Пункты меню
        for index, item in enumerate(self._items):
            item_is_selected: bool = index == self._selected_index

            item_rect = pygame.Rect(
                content_rect.left,
                y_cursor,
                content_rect.width,
                MENU_ITEM_HEIGHT,
            )

            if item_is_selected:
                pygame.draw.rect(
                    surface,
                    self._theme.menu_highlight_color,
                    item_rect,
                    border_radius=MENU_CORNER_RADIUS,
                )

            label_surface = self._item_font.render(
                item.label,
                True,
                self._theme.menu_text_color,
            )
            label_rect = label_surface.get_rect()
            label_rect.centery = item_rect.centery
            label_rect.centerx = content_rect.centerx

            surface.blit(label_surface, label_rect)

            y_cursor = item_rect.bottom + MENU_ITEM_VERTICAL_SPACING


class MainMenuView(BaseMenuView):
    """Главное меню игры."""

    def __init__(self, theme: Theme) -> None:
        items = [
            MenuItem("Новая игра: новичок", "new_game_beginner"),
            MenuItem("Новая игра: любитель", "new_game_intermediate"),
            MenuItem("Новая игра: эксперт", "new_game_expert"),
            MenuItem("Настройки (в разработке)", "settings"),
            MenuItem("Кампания (в разработке)", "campaign"),
            MenuItem("Выход", "exit"),
        ]
        super().__init__(title="Minesweeper", items=items, theme=theme)


class PauseMenuView(BaseMenuView):
    """Меню паузы, отображаемое поверх игры."""

    def __init__(self, theme: Theme) -> None:
        items = [
            MenuItem("Продолжить", "resume"),
            MenuItem("Новая игра", "restart"),
            MenuItem("В главное меню", "main_menu"),
        ]
        super().__init__(title="Пауза", items=items, theme=theme)


class GameOverMenuView(BaseMenuView):
    """Меню результата игры (победа / поражение)."""

    def __init__(self, theme: Theme) -> None:
        items = [
            MenuItem("Новая игра", "restart"),
            MenuItem("В главное меню", "main_menu"),
        ]
        super().__init__(title="Результат игры", items=items, theme=theme)
