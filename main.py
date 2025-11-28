"""Точка входа для игры Minesweeper на Python + pygame.

Этот модуль просто создаёт экземпляр GameApp и запускает его.
Вся логика, меню, сессии и отрисовка — в модулях ui/ и game/.
"""

from __future__ import annotations

from ui.main_window import GameApp


def main() -> None:
    """Запустить игровое приложение."""
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()
