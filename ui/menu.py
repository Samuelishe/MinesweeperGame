"""Simple menu views for the Minesweeper game."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from ui.themes import (
    MENU_NOISE_KEY,
    MENU_PANEL_FRAME_KEY,
    MENU_SELECTOR_ARROW_KEY,
    Theme,
)

Color = Tuple[int, int, int]


# =========================
# Layout / style constants
# =========================
MENU_WIDTH_RATIO: float = 0.62
MENU_HEIGHT_RATIO: float = 0.82
MENU_SCREEN_MARGIN: int = 28

# Панель “стекло” (внутренняя подложка под текст)
MENU_CORNER_RADIUS: int = 18
MENU_PANEL_INSET: int = 18
MENU_PANEL_ALPHA: int = 170

# Тёмный затемнённый слой (поверх фона, под меню)
MENU_BACKDROP_ALPHA: int = 110

# Тень панели
MENU_SHADOW_ALPHA: int = 115
MENU_SHADOW_OFFSET: Tuple[int, int] = (10, 12)
MENU_SHADOW_BLUR_SCALE: float = 0.40

# Шум поверх панели
MENU_NOISE_ALPHA: int = 22

# Safe-area под декоративную рамку (под конкретный арт!)
# Это именно “внутренний контент”, куда можно класть текст/кнопки.
MENU_FRAME_SAFE_LEFT: int = 64
MENU_FRAME_SAFE_RIGHT: int = 64
MENU_FRAME_SAFE_TOP: int = 92
MENU_FRAME_SAFE_BOTTOM: int = 74

# Заголовок/подзаголовок/пункты
MENU_TITLE_FONT_SIZE: int = 44
MENU_SUBTITLE_FONT_SIZE: int = 24
MENU_ITEM_FONT_SIZE: int = 30

MENU_TITLE_MARGIN_BOTTOM: int = 18
MENU_SUBTITLE_MARGIN_BOTTOM: int = 10

# Пункты меню
MENU_ITEM_HEIGHT: int = 52
MENU_ITEM_VERTICAL_SPACING: int = 12

# Подсветка выбранного пункта (можно оставить даже при стрелке — это “плашка”)
MENU_HIGHLIGHT_ALPHA: int = 70
MENU_HIGHLIGHT_OUTLINE_ALPHA: int = 130
MENU_HIGHLIGHT_RADIUS: int = 14
MENU_HIGHLIGHT_OUTLINE_WIDTH: int = 1

# Маркер выбора
# Ключевая штука: фиксируем колонку слева под маркер — текст не прыгает.
MENU_MARKER_RESERVED_WIDTH: int = 56
MENU_MARKER_MAX_HEIGHT_RATIO: float = 0.55  # от высоты item_rect
MENU_MARKER_LEFT_PADDING: int = 16
MENU_LABEL_LEFT_PADDING: int = 10

# Если “стрелка” слишком широкая — это орнамент, а не маркер.
MENU_MARKER_MAX_ASPECT_RATIO: float = 2.2


@dataclass(slots=True)
class MenuItem:
    """Один пункт меню."""

    label: str
    action_id: str


class BaseMenuView:
    """Базовый класс для простых вертикальных меню."""

    _shadow_cache: Dict[Tuple[int, int, int, int], pygame.Surface] = {}
    _scaled_cache: Dict[Tuple[int, int, int, int], pygame.Surface] = {}
    _noise_cache: Dict[Tuple[int, int, int, int], pygame.Surface] = {}

    def __init__(
        self,
        title: str,
        items: Sequence[MenuItem],
        theme: Theme,
        subtitle_lines: Optional[Sequence[str]] = None,
    ) -> None:
        self._title = title
        self._items = list(items)
        self._theme = theme
        self._subtitle_lines = list(subtitle_lines or [])

        self._selected_index = 0
        self._hover_index: Optional[int] = None

        self._is_dragging = False
        self._drag_offset = (0, 0)
        self._drag_rect: Optional[pygame.Rect] = None

        self._layout_item_rects: List[pygame.Rect] = []
        self._layout_menu_rect: pygame.Rect = pygame.Rect(0, 0, 1, 1)
        self._layout_content_rect: pygame.Rect = pygame.Rect(0, 0, 1, 1)

        self._title_font = self._get_ui_font(MENU_TITLE_FONT_SIZE)
        self._subtitle_font = self._get_ui_font(MENU_SUBTITLE_FONT_SIZE)
        self._item_font = self._get_ui_font(MENU_ITEM_FONT_SIZE)

    # -----------------------------
    # Public input API
    # -----------------------------
    def set_selected_index(self, index: int) -> None:
        self._selected_index = max(0, min(index, len(self._items) - 1))

    def on_mouse_motion(self, pos: Tuple[int, int]) -> None:
        if self._is_dragging and self._drag_rect is not None:
            new_left = pos[0] - self._drag_offset[0]
            new_top = pos[1] - self._drag_offset[1]
            self._layout_menu_rect = pygame.Rect(
                new_left,
                new_top,
                self._layout_menu_rect.width,
                self._layout_menu_rect.height,
            )
            return

        self._hover_index = None
        for idx, rect in enumerate(self._layout_item_rects):
            if rect.collidepoint(pos):
                self._hover_index = idx
                self._selected_index = idx
                break

    def on_mouse_down(self, pos: Tuple[int, int], button: int) -> None:
        if button != 1:
            return

        # Drag — по панели целиком
        if self._layout_menu_rect.collidepoint(pos):
            self._is_dragging = True
            self._drag_offset = (pos[0] - self._layout_menu_rect.left, pos[1] - self._layout_menu_rect.top)
            self._drag_rect = self._layout_menu_rect

    def on_mouse_up(self, pos: Tuple[int, int], button: int) -> Optional[str]:
        if button != 1:
            return None

        was_dragging = self._is_dragging
        self._is_dragging = False
        self._drag_rect = None

        # Если это был drag — клика не делаем
        if was_dragging:
            return None

        for idx, rect in enumerate(self._layout_item_rects):
            if rect.collidepoint(pos):
                self._selected_index = idx
                return self._items[idx].action_id

        return None

    def on_key_down(self, key: int) -> Optional[str]:
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

    def reset_selection(self) -> None:
        """Сбросить выбор/hover и выбрать первый доступный пункт."""
        self._hover_index = None
        self._selected_index = 0

        # Если у тебя есть disabled-пункты и логика "пропускать", можно усилить:
        # while self._selected_index < len(self._items) and not self._items[self._selected_index].enabled:
        #     self._selected_index += 1
        # if self._selected_index >= len(self._items):
        #     self._selected_index = 0


    # -----------------------------
    # Drawing
    # -----------------------------
    def draw(self, surface: pygame.Surface) -> None:
        screen_rect = surface.get_rect()
        menu_rect, content_rect, item_rects = self._calculate_layout(screen_rect)

        self._layout_menu_rect = menu_rect
        self._layout_content_rect = content_rect
        self._layout_item_rects = item_rects

        # Backdrop
        backdrop = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
        backdrop.fill((0, 0, 0, MENU_BACKDROP_ALPHA))
        surface.blit(backdrop, (0, 0))

        # Panel + frame
        self._draw_panel(surface=surface, menu_rect=menu_rect)

        # Title
        y_cursor = content_rect.top
        title_surf = self._title_font.render(self._title, True, self._theme.menu_text_color)
        title_x = content_rect.centerx - title_surf.get_width() // 2
        surface.blit(title_surf, (title_x, y_cursor))
        y_cursor += title_surf.get_height() + MENU_TITLE_MARGIN_BOTTOM

        # Subtitles
        for line in self._subtitle_lines:
            line_surf = self._subtitle_font.render(line, True, self._theme.menu_text_color)
            line_x = content_rect.centerx - line_surf.get_width() // 2
            surface.blit(line_surf, (line_x, y_cursor))
            y_cursor += line_surf.get_height() + 6

        if self._subtitle_lines:
            y_cursor += MENU_SUBTITLE_MARGIN_BOTTOM

        # Items
        for idx, item_rect in enumerate(item_rects):
            is_selected = idx == self._selected_index
            is_hover = idx == self._hover_index

            if is_selected or is_hover:
                self._draw_item_highlight(surface=surface, rect=item_rect)

            # фиксированная колонка маркера (чтобы текст не прыгал)
            marker_area_left = item_rect.left
            marker_area_width = MENU_MARKER_RESERVED_WIDTH

            label_left = marker_area_left + marker_area_width + MENU_LABEL_LEFT_PADDING
            label_rect = pygame.Rect(
                label_left,
                item_rect.top,
                max(1, item_rect.right - label_left),
                item_rect.height,
            )

            # Marker — только для выбранного пункта (но место зарезервировано всегда)
            if is_selected:
                self._draw_marker(surface=surface, rect=item_rect)

            label_color = self._theme.menu_text_color
            label_surf = self._item_font.render(self._items[idx].label, True, label_color)

            label_x = label_rect.left
            label_y = item_rect.centery - label_surf.get_height() // 2
            surface.blit(label_surf, (label_x, label_y))

    # -----------------------------
    # Layout helpers
    # -----------------------------
    def _calculate_layout(
        self,
        screen_rect: pygame.Rect,
    ) -> Tuple[pygame.Rect, pygame.Rect, List[pygame.Rect]]:
        sw, sh = screen_rect.size
        max_w = max(1, sw - 2 * MENU_SCREEN_MARGIN)
        max_h = max(1, sh - 2 * MENU_SCREEN_MARGIN)

        # Базово: хотим ширину как долю экрана, но не вылезать по высоте
        target_w = int(max_w * MENU_WIDTH_RATIO)
        target_h = int(max_h * MENU_HEIGHT_RATIO)

        # Если есть декоративная рамка — стараемся сохранить её аспект
        frame = self._theme.sprites.get(MENU_PANEL_FRAME_KEY)
        frame_aspect: Optional[float] = None
        if frame is not None:
            fw, fh = frame.get_size()
            if fw > 0 and fh > 0:
                frame_aspect = fw / fh

        if frame_aspect is not None:
            # Сначала пробуем по ширине, потом по высоте.
            menu_w = max(1, min(target_w, max_w))
            menu_h = max(1, int(menu_w / frame_aspect))

            if menu_h > target_h:
                menu_h = max(1, min(target_h, max_h))
                menu_w = max(1, int(menu_h * frame_aspect))

            menu_w = min(menu_w, max_w)
            menu_h = min(menu_h, max_h)
        else:
            menu_w = max(1, min(target_w, max_w))
            menu_h = max(1, min(target_h, max_h))

        menu_rect = pygame.Rect(0, 0, menu_w, menu_h)
        menu_rect.center = screen_rect.center

        # Внутренняя панель (glass) — чуть меньше, чтобы у рамки был “воздух”
        panel_rect = menu_rect.inflate(-2 * MENU_PANEL_INSET, -2 * MENU_PANEL_INSET)

        # Внутренний контент внутри рамки
        content_rect = pygame.Rect(
            panel_rect.left + MENU_FRAME_SAFE_LEFT,
            panel_rect.top + MENU_FRAME_SAFE_TOP,
            max(1, panel_rect.width - MENU_FRAME_SAFE_LEFT - MENU_FRAME_SAFE_RIGHT),
            max(1, panel_rect.height - MENU_FRAME_SAFE_TOP - MENU_FRAME_SAFE_BOTTOM),
        )

        # ---- Vertical sizing: если не влезает, ужимаем spacing/height ----
        item_h = MENU_ITEM_HEIGHT
        spacing = MENU_ITEM_VERTICAL_SPACING

        title_h = self._title_font.get_height()
        subtitle_h = 0
        if self._subtitle_lines:
            subtitle_h = sum(self._subtitle_font.get_height() + 6 for _ in self._subtitle_lines)
            subtitle_h += MENU_SUBTITLE_MARGIN_BOTTOM

        def total_needed_height() -> int:
            items_h = len(self._items) * item_h
            gaps_h = max(0, len(self._items) - 1) * spacing
            return title_h + MENU_TITLE_MARGIN_BOTTOM + subtitle_h + items_h + gaps_h

        # Ужимаем только то, что безопасно: item_h и spacing (не уходим в минус)
        min_item_h = 28
        min_spacing = 4
        while total_needed_height() > content_rect.height and (item_h > min_item_h or spacing > min_spacing):
            if spacing > min_spacing:
                spacing -= 1
            elif item_h > min_item_h:
                item_h -= 1
            else:
                break

        # Вертикальная центровка контент-блока в content_rect
        needed = total_needed_height()
        extra = max(0, content_rect.height - needed)
        y_cursor = content_rect.top + extra // 2

        # Title rect (используем только для вычисления y_cursor)
        y_cursor += title_h + MENU_TITLE_MARGIN_BOTTOM
        if self._subtitle_lines:
            y_cursor += subtitle_h

        # Item rects
        item_rects: List[pygame.Rect] = []
        for _ in self._items:
            rect = pygame.Rect(content_rect.left, y_cursor, content_rect.width, max(1, item_h))
            item_rects.append(rect)
            y_cursor += item_h + spacing

        return menu_rect, content_rect, item_rects

    # -----------------------------
    # Style drawing helpers
    # -----------------------------
    def _draw_panel(self, surface: pygame.Surface, menu_rect: pygame.Rect) -> None:
        if menu_rect.width <= 1 or menu_rect.height <= 1:
            return

        panel_rect = menu_rect.inflate(-2 * MENU_PANEL_INSET, -2 * MENU_PANEL_INSET)
        panel_rect.width = max(1, panel_rect.width)
        panel_rect.height = max(1, panel_rect.height)

        # Shadow
        self._draw_soft_shadow(surface=surface, rect=panel_rect)

        # Glass panel
        panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 0))

        pygame.draw.rect(
            panel_surf,
            self._with_alpha(self._theme.menu_background_color, MENU_PANEL_ALPHA),
            pygame.Rect(0, 0, panel_rect.width, panel_rect.height),
            border_radius=MENU_CORNER_RADIUS,
        )

        # Noise
        noise = self._theme.sprites.get(MENU_NOISE_KEY)
        if noise is not None:
            noise_prepared = self._prepare_noise_surface(noise)
            tiled = self._get_tiled_noise(size=panel_rect.size, noise=noise_prepared)
            tiled.set_alpha(MENU_NOISE_ALPHA)
            panel_surf.blit(tiled, (0, 0))

        surface.blit(panel_surf, panel_rect.topleft)

        # Decorative frame: масштабируем только в положительные размеры
        frame = self._theme.sprites.get(MENU_PANEL_FRAME_KEY)
        if frame is not None:
            w = max(1, menu_rect.width)
            h = max(1, menu_rect.height)
            frame_scaled = self._get_scaled_cached(frame, (w, h))
            surface.blit(frame_scaled, menu_rect.topleft)

    def _draw_item_highlight(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        if rect.width <= 1 or rect.height <= 1:
            return
        w = rect.width
        h = rect.height
        if w <= 2 or h <= 2:
            return

        highlight = pygame.Surface((w, h), pygame.SRCALPHA)
        highlight.fill((0, 0, 0, 0))

        pygame.draw.rect(
            highlight,
            self._with_alpha(self._theme.menu_highlight_color, MENU_HIGHLIGHT_ALPHA),
            pygame.Rect(0, 0, w, h),
            border_radius=MENU_HIGHLIGHT_RADIUS,
        )
        pygame.draw.rect(
            highlight,
            self._with_alpha(self._theme.menu_border_color, MENU_HIGHLIGHT_OUTLINE_ALPHA),
            pygame.Rect(0, 0, w, h),
            width=MENU_HIGHLIGHT_OUTLINE_WIDTH,
            border_radius=MENU_HIGHLIGHT_RADIUS,
        )

        surface.blit(highlight, rect.topleft)

    def _draw_marker(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        max_h = max(1, int(rect.height * MENU_MARKER_MAX_HEIGHT_RATIO))
        marker = self._get_menu_marker_surface(max_h)
        if marker is None:
            return

        marker_w, marker_h = marker.get_size()
        if marker_w <= 0 or marker_h <= 0:
            return

        x = rect.left + MENU_MARKER_LEFT_PADDING
        y = rect.centery - marker_h // 2
        surface.blit(marker, (x, y))

    # -----------------------------
    # Font / caching utils
    # -----------------------------
    def _get_ui_font(self, size: int) -> pygame.font.Font:
        """UI-шрифт (не эмодзи). Берём из assets/fonts, с fallback на системный."""
        font_path = Path(self._resolve_asset_path(self._theme.ui_font_path))

        if font_path.is_file():
            return pygame.font.Font(str(font_path), size)

        # Fallback, чтобы игра вообще запускалась даже без файла.
        return pygame.font.SysFont(None, size)


    @staticmethod
    def _get_assets_dir() -> Path:
        """Путь к папке assets/ (ui находится в ui/, поэтому parents[1])."""
        return Path(__file__).resolve().parents[1] / "assets"

    def _resolve_asset_path(self, relative_path: str) -> str:
        """Преобразовать путь относительно assets/ в абсолютный путь."""
        return str(self._get_assets_dir() / relative_path)


    @staticmethod
    def _prepare_noise_surface(noise: pygame.Surface) -> pygame.Surface:
        prepared = noise
        flags = prepared.get_flags()
        has_per_pixel_alpha = bool(flags & pygame.SRCALPHA)

        if not has_per_pixel_alpha:
            prepared = prepared.convert()
            prepared.set_colorkey((0, 0, 0))
            prepared = prepared.convert_alpha()

        return prepared

    def _get_tiled_noise(self, size: Tuple[int, int], noise: pygame.Surface) -> pygame.Surface:
        w, h = size
        w = max(1, w)
        h = max(1, h)

        key = (w, h, MENU_CORNER_RADIUS, id(noise))
        cached = self._noise_cache.get(key)
        if cached is not None:
            return cached.copy()

        tiled = pygame.Surface((w, h), pygame.SRCALPHA)
        nw, nh = noise.get_size()
        nw = max(1, nw)
        nh = max(1, nh)

        for y in range(0, h, nh):
            for x in range(0, w, nw):
                tiled.blit(noise, (x, y))

        self._noise_cache[key] = tiled
        return tiled.copy()

    def _draw_soft_shadow(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        w = max(1, rect.width)
        h = max(1, rect.height)

        key = (w, h, MENU_CORNER_RADIUS, MENU_SHADOW_ALPHA)
        shadow = self._shadow_cache.get(key)

        if shadow is None:
            base = pygame.Surface((w, h), pygame.SRCALPHA)
            base.fill((0, 0, 0, 0))
            pygame.draw.rect(
                base,
                (0, 0, 0, MENU_SHADOW_ALPHA),
                pygame.Rect(0, 0, w, h),
                border_radius=MENU_CORNER_RADIUS,
            )

            w_small = max(1, int(w * MENU_SHADOW_BLUR_SCALE))
            h_small = max(1, int(h * MENU_SHADOW_BLUR_SCALE))
            small = pygame.transform.smoothscale(base, (w_small, h_small))
            shadow = pygame.transform.smoothscale(small, (w, h))

            self._shadow_cache[key] = shadow

        surface.blit(shadow, (rect.left + MENU_SHADOW_OFFSET[0], rect.top + MENU_SHADOW_OFFSET[1]))

    def _get_menu_marker_surface(self, max_height: int) -> Optional[pygame.Surface]:
        arrow = self._theme.sprites.get(MENU_SELECTOR_ARROW_KEY)
        if arrow is not None:
            width, height = arrow.get_size()
            if width > 0 and height > 0:
                aspect = width / max(1, height)
                if aspect <= MENU_MARKER_MAX_ASPECT_RATIO:
                    if height <= max_height:
                        return arrow
                    new_w = max(1, int(width * (max_height / height)))
                    return self._get_scaled_cached(arrow, (new_w, max_height))

        marker_surface = self._item_font.render("▸", True, self._theme.menu_text_color)
        if marker_surface.get_width() <= 0:
            return None
        return marker_surface

    def _get_scaled_cached(self, surface: pygame.Surface, size: Tuple[int, int]) -> pygame.Surface:
        width, height = size
        if width <= 1 or height <= 1:
            return surface
        w = max(1, size[0])
        h = max(1, size[1])

        key = (id(surface), w, h, surface.get_flags() & pygame.SRCALPHA)
        cached = self._scaled_cache.get(key)
        if cached is not None:
            return cached

        scaled = pygame.transform.smoothscale(surface, (w, h))
        self._scaled_cache[key] = scaled
        return scaled

    @staticmethod
    def _with_alpha(color: Color, alpha: int) -> Tuple[int, int, int, int]:
        r, g, b = color
        return r, g, b, alpha


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
