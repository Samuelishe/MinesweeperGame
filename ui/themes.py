"""Темы оформления (палитры и пути к ассетам)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


Color = Tuple[int, int, int]


@dataclass(slots=True)
class Theme:
    """Тема интерфейса.

    Важно: тут только данные. pygame-объекты (Surface/Font) не храним.
    """

    # --- базовые цвета UI ---
    background_color: Color
    menu_text_color: Color
    menu_muted_text_color: Color
    menu_highlight_text_color: Color

    menu_overlay_color: Tuple[int, int, int, int]
    menu_highlight_color: Tuple[int, int, int, int]
    menu_border_color: Tuple[int, int, int, int]

    # --- пути к ассетам (опционально) ---
    ui_font_path: Optional[str] = None
    emoji_font_path: Optional[str] = None

    menu_background_image_path: Optional[str] = None
    menu_frame_image_path: Optional[str] = None
    menu_noise_image_path: Optional[str] = None
    menu_selector_icon_path: Optional[str] = None

    # --- параметры меню ---
    menu_screen_margin_px: int = 56
    menu_max_width_ratio: float = 0.86
    menu_max_height_ratio: float = 0.82

    # внутренние отступы контента (внутри художественной рамки)
    menu_content_padding_px: int = 56
    menu_item_height_px: int = 64
    menu_item_gap_px: int = 18

    menu_title_gap_px: int = 18
    menu_subtitle_gap_px: int = 12

    # резерв под стрелку/иконку слева, чтобы текст не "ездил"
    menu_selector_reserved_px: int = 44


def _asset_path(*parts: str) -> str:
    """Построить путь к ассету относительно корня проекта.

    Предположение: themes.py лежит в ui/, рядом с main_window.py и т.д.
    Тогда корень проекта = родитель папки ui.
    """
    ui_dir = Path(__file__).resolve().parent
    project_root = ui_dir.parent
    return str(project_root.joinpath(*parts))


def _existing_or_none(path: str) -> Optional[str]:
    """Вернуть путь, если файл существует, иначе None."""
    if Path(path).is_file():
        return path
    return None


def create_default_theme() -> Theme:
    """Тема по умолчанию (безопасна даже если ассеты не на месте)."""
    ui_font = _existing_or_none(
        _asset_path("assets", "fonts", "Inter-VariableFont_opsz,wght.ttf")
    )
    emoji_font = _existing_or_none(
        _asset_path("assets", "fonts", "NotoColorEmoji.ttf")
    )

    bg = _existing_or_none(_asset_path("assets", "images", "bg_main.png"))
    frame = _existing_or_none(_asset_path("assets", "images", "panel_frame.png"))
    noise = _existing_or_none(_asset_path("assets", "images", "noise.png"))
    selector = _existing_or_none(_asset_path("assets", "images", "selector_arrow.png"))

    return Theme(
        background_color=(24, 24, 24),
        menu_text_color=(235, 235, 235),
        menu_muted_text_color=(200, 200, 200),
        menu_highlight_text_color=(255, 255, 255),
        menu_overlay_color=(0, 0, 0, 140),
        menu_highlight_color=(95, 120, 170, 120),
        menu_border_color=(255, 255, 255, 40),
        ui_font_path=ui_font,
        emoji_font_path=emoji_font,
        menu_background_image_path=bg,
        menu_frame_image_path=frame,
        menu_noise_image_path=noise,
        menu_selector_icon_path=selector,
    )
