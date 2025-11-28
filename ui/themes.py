"""Темы оформления игры Сапёр.

Модуль описывает структуру темы (Theme), которая используется рендерером
для отрисовки поля, чисел, мин, флагов, HUD и меню. Тема может быть как
чисто программной (цвета, линии, шрифты), так и спрайтовой (PNG).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

import pygame


Color = Tuple[int, int, int]


@dataclass(slots=True)
class Theme:
    """Тема оформления игры.

    Attributes:
        name:
            Имя темы (для настроек и логирования).

        background_color:
            Цвет фона окна.
        board_background_color:
            Цвет фона области с полем.

        tile_hidden_color:
            Цвет закрытых клеток.
        tile_revealed_color:
            Цвет открытых клеток.
        tile_border_color:
            Цвет рамок клеток.

        mine_color:
            Цвет мины, если используется программная отрисовка.
        flag_color:
            Цвет флага, если используется программная отрисовка.

        hud_background_color:
            Цвет фона HUD (панель сверху).
        hud_text_color:
            Цвет текста HUD (цифры, статус).

        menu_shadow_color:
            Цвет тени под прямоугольником меню.
        menu_background_color:
            Цвет фона прямоугольника меню.
        menu_border_color:
            Цвет рамки меню.
        menu_text_color:
            Цвет текста в меню.
        menu_highlight_color:
            Цвет подсветки выбранного пункта меню.

        number_colors:
            Цвета чисел 1–8. Остальные значения по умолчанию рисуются
            цветом hud_text_color.

        use_sprites_for_tiles:
            Использовать ли спрайты для тайлов вместо программной отрисовки.
        use_sprites_for_icons:
            Использовать ли спрайты для иконок (мины, флаги, смайлик).

        sprites:
            Словарь с заранее загруженными Surface для различных сущностей.
    """

    name: str

    background_color: Color
    board_background_color: Color

    tile_hidden_color: Color
    tile_revealed_color: Color
    tile_border_color: Color

    mine_color: Color
    flag_color: Color

    hud_background_color: Color
    hud_text_color: Color

    menu_shadow_color: Color
    menu_background_color: Color
    menu_border_color: Color
    menu_text_color: Color
    menu_highlight_color: Color

    number_colors: Dict[int, Color] = field(default_factory=dict)

    use_sprites_for_tiles: bool = False
    use_sprites_for_icons: bool = False

    sprites: Dict[str, pygame.Surface] = field(default_factory=dict)

    def get_number_color(self, value: int) -> Color:
        """Получить цвет числа на клетке.

        Args:
            value:
                Число соседних мин (1–8).

        Returns:
            Цвет, соответствующий этому числу, либо цвет текста HUD
            по умолчанию.
        """
        return self.number_colors.get(value, self.hud_text_color)


def create_default_theme() -> Theme:
    """Создать классическую тему по умолчанию.

    Возвращает строго программную тему без спрайтов, в стиле
    «серые клетки + цветные цифры».
    """
    background_color: Color = (192, 192, 192)
    board_background_color: Color = (192, 192, 192)

    tile_hidden_color: Color = (160, 160, 160)
    tile_revealed_color: Color = (224, 224, 224)
    tile_border_color: Color = (128, 128, 128)

    mine_color: Color = (0, 0, 0)
    flag_color: Color = (220, 0, 0)

    hud_background_color: Color = (160, 160, 160)
    hud_text_color: Color = (0, 0, 0)

    # Меню делаем чуть более контрастным, но в той же палитре.
    menu_shadow_color: Color = (96, 96, 96)
    menu_background_color: Color = (208, 208, 208)
    menu_border_color: Color = (64, 64, 64)
    menu_text_color: Color = (0, 0, 0)
    menu_highlight_color: Color = (176, 196, 222)  # light steel blue vibe

    number_colors: Dict[int, Color] = {
        1: (0, 0, 255),
        2: (0, 128, 0),
        3: (255, 0, 0),
        4: (0, 0, 128),
        5: (128, 0, 0),
        6: (0, 128, 128),
        7: (0, 0, 0),
        8: (128, 128, 128),
    }

    return Theme(
        name="Classic",
        background_color=background_color,
        board_background_color=board_background_color,
        tile_hidden_color=tile_hidden_color,
        tile_revealed_color=tile_revealed_color,
        tile_border_color=tile_border_color,
        mine_color=mine_color,
        flag_color=flag_color,
        hud_background_color=hud_background_color,
        hud_text_color=hud_text_color,
        menu_shadow_color=menu_shadow_color,
        menu_background_color=menu_background_color,
        menu_border_color=menu_border_color,
        menu_text_color=menu_text_color,
        menu_highlight_color=menu_highlight_color,
        number_colors=number_colors,
        use_sprites_for_tiles=False,
        use_sprites_for_icons=False,
        sprites={},
    )
