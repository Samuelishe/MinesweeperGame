"""Главное окно и игровой цикл для Сапёра на pygame."""

from __future__ import annotations

from typing import Tuple

import pygame

from core.enums import DifficultyLevel, GameStatus
from core.settings import DEFAULT_DIFFICULTIES
from game.app_state import AppScreen, AppStateManager
from game.rules import ClassicMinesweeperRules
from game.session import GameSession, SessionSettings
from ui.events import handle_mouse_button_down
from ui.menu import GameOverMenuView, MainMenuView, PauseMenuView
from ui.renderer import BoardRenderer, LayoutInfo
from ui.themes import create_default_theme


WINDOW_CAPTION: str = "Minesweeper"
TARGET_FPS: int = 60

# Минимальный удобный стартовый размер окна.
START_WINDOW_MIN_WIDTH: int = 640
START_WINDOW_MIN_HEIGHT: int = 480


class GameApp:
    """Приложение Сапёра на pygame."""

    def __init__(self) -> None:
        """Инициализировать приложение, pygame и начальные объекты."""
        pygame.init()
        pygame.display.set_caption(WINDOW_CAPTION)

        self._clock: pygame.time.Clock = pygame.time.Clock()
        self._app_state_manager = AppStateManager()

        # Важно: создаём окно до загрузки спрайтов, чтобы можно было
        # безопасно делать convert_alpha().
        self._window: pygame.Surface = pygame.display.set_mode(
            (START_WINDOW_MIN_WIDTH, START_WINDOW_MIN_HEIGHT),
            pygame.RESIZABLE,
        )

        self._theme = create_default_theme(display_surface=self._window)
        self._renderer = BoardRenderer(theme=self._theme)

        self._main_menu_view = MainMenuView(theme=self._theme)
        self._pause_menu_view = PauseMenuView(theme=self._theme)
        self._game_over_menu_view = GameOverMenuView(theme=self._theme)

        self._running: bool = True

        # Подготовим стартовую сессию, чтобы подобрать размер окна…
        self._setup_initial_session_and_window()
        # …но начинать будем с главного меню, а не с игры.
        self._app_state_manager.go_to_main_menu()
        self._main_menu_view.reset_selection()

    def _setup_initial_session_and_window(self) -> None:  # type: ignore[override]
        """Создать начальную игровую сессию и окно подходящего размера."""
        difficulty_config = DEFAULT_DIFFICULTIES[DifficultyLevel.BEGINNER]

        session_settings = SessionSettings(
            width=difficulty_config.width,
            height=difficulty_config.height,
            mine_count=difficulty_config.mine_count,
        )

        rules = ClassicMinesweeperRules()
        self._app_state_manager.start_game(
            settings=session_settings,
            rules=rules,
        )

        session = self._app_state_manager.state.session
        if session is None:
            raise RuntimeError("Не удалось создать начальную игровую сессию.")

        min_width, min_height = self._renderer.calculate_min_window_size(
            board=session.board,
        )

        window_width = max(min_width, START_WINDOW_MIN_WIDTH)
        window_height = max(min_height, START_WINDOW_MIN_HEIGHT)

        self._window = pygame.display.set_mode(
            (window_width, window_height),
            pygame.RESIZABLE,
        )

    def run(self) -> None:
        """Запустить главный цикл приложения."""
        while self._running:
            self._process_events()
            self._update()
            self._draw()
            self._clock.tick(TARGET_FPS)

        pygame.quit()

    # === Обработка событий ===

    def _process_events(self) -> None:
        """Обработать события pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_button_down(event)

            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event)

            elif event.type == pygame.MOUSEBUTTONUP:
                self._handle_mouse_button_up(event)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Обработать нажатие клавиши."""
        state = self._app_state_manager.state

        if event.key == pygame.K_ESCAPE:
            self._handle_escape()
            return

        if event.key == pygame.K_F11:
            self._toggle_fullscreen()
            return

        # Управление меню стрелками и Enter/Space
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if state.current_screen is AppScreen.MAIN_MENU:
                action_id = self._main_menu_view.confirm_selection()
                if action_id is not None:
                    self._handle_menu_action(action_id)
            elif state.current_screen is AppScreen.PAUSE_MENU:
                action_id = self._pause_menu_view.confirm_selection()
                if action_id is not None:
                    self._handle_menu_action(action_id)
            elif state.current_screen is AppScreen.GAME_OVER:
                action_id = self._game_over_menu_view.confirm_selection()
                if action_id is not None:
                    self._handle_menu_action(action_id)
            return

        if event.key in (pygame.K_UP, pygame.K_DOWN):
            if state.current_screen is AppScreen.MAIN_MENU:
                if event.key == pygame.K_UP:
                    self._main_menu_view.move_selection_up()
                else:
                    self._main_menu_view.move_selection_down()
            elif state.current_screen is AppScreen.PAUSE_MENU:
                if event.key == pygame.K_UP:
                    self._pause_menu_view.move_selection_up()
                else:
                    self._pause_menu_view.move_selection_down()
            elif state.current_screen is AppScreen.GAME_OVER:
                if event.key == pygame.K_UP:
                    self._game_over_menu_view.move_selection_up()
                else:
                    self._game_over_menu_view.move_selection_down()

    def _handle_resize(self, event: pygame.event.Event) -> None:
        """Обработать изменение размера окна."""
        new_size: Tuple[int, int] = (event.w, event.h)
        self._window = pygame.display.set_mode(new_size, pygame.RESIZABLE)

    def _handle_mouse_button_down(self, event: pygame.event.Event) -> None:
        """Обработать клик мышью.

        Правило:
            * если активен экран меню — клик обрабатывает меню;
            * иначе (GAME) — клик обрабатывает поле.
        """
        state = self._app_state_manager.state

        if state.current_screen is AppScreen.MAIN_MENU:
            action_id = self._main_menu_view.handle_mouse_button_down(
                surface=self._window,
                mouse_pos=event.pos,
                button=event.button,
            )
            if action_id is not None:
                self._handle_menu_action(action_id)
            return

        if state.current_screen is AppScreen.PAUSE_MENU:
            action_id = self._pause_menu_view.handle_mouse_button_down(
                surface=self._window,
                mouse_pos=event.pos,
                button=event.button,
            )
            if action_id is not None:
                self._handle_menu_action(action_id)
            return

        if state.current_screen is AppScreen.GAME_OVER:
            action_id = self._game_over_menu_view.handle_mouse_button_down(
                surface=self._window,
                mouse_pos=event.pos,
                button=event.button,
            )
            if action_id is not None:
                self._handle_menu_action(action_id)
            return

        session = state.session
        if session is None:
            return

        layout = self._get_current_layout(session=session)

        _ = handle_mouse_button_down(
            event=event,
            app_state_manager=self._app_state_manager,
            session=session,
            layout=layout,
        )

    def _handle_escape(self) -> None:
        """Обработка клавиши ESC."""
        state = self._app_state_manager.state

        if state.current_screen is AppScreen.GAME:
            self._app_state_manager.pause_game()
        elif state.current_screen is AppScreen.PAUSE_MENU:
            self._app_state_manager.resume_game()
        elif state.current_screen is AppScreen.GAME_OVER:
            self._app_state_manager.abort_to_main_menu()
        elif state.current_screen is AppScreen.MAIN_MENU:
            self._running = False

    def _handle_mouse_motion(self, event: pygame.event.Event) -> None:
        """Обработать движение мыши (hover по меню)."""
        state = self._app_state_manager.state
        mouse_pos = event.pos

        if state.current_screen is AppScreen.MAIN_MENU:
            self._main_menu_view.handle_mouse_motion(self._window, mouse_pos)
        elif state.current_screen is AppScreen.PAUSE_MENU:
            self._pause_menu_view.handle_mouse_motion(self._window, mouse_pos)
        elif state.current_screen is AppScreen.GAME_OVER:
            self._game_over_menu_view.handle_mouse_motion(self._window, mouse_pos)

    def _handle_mouse_button_up(self, _event: pygame.event.Event) -> None:
        """Обработать отпускание кнопки мыши (завершение drag меню)."""
        state = self._app_state_manager.state

        if state.current_screen is AppScreen.MAIN_MENU:
            self._main_menu_view.handle_mouse_button_up()
        elif state.current_screen is AppScreen.PAUSE_MENU:
            self._pause_menu_view.handle_mouse_button_up()
        elif state.current_screen is AppScreen.GAME_OVER:
            self._game_over_menu_view.handle_mouse_button_up()

    def _toggle_fullscreen(self) -> None:
        """Переключить полноэкранный режим."""
        flags = self._window.get_flags()
        is_fullscreen = bool(flags & pygame.FULLSCREEN)

        if is_fullscreen:
            pygame.display.set_mode(self._window.get_size(), pygame.RESIZABLE)
        else:
            display_info = pygame.display.Info()
            pygame.display.set_mode(
                (display_info.current_w, display_info.current_h),
                pygame.FULLSCREEN,
            )

    # === Логика обновления и отрисовки ===

    def _update(self) -> None:
        """Обновить состояние игры (проверка конца игры)."""
        state = self._app_state_manager.state
        session = state.session

        if session is None:
            return

        if (
            session.status in (GameStatus.WON, GameStatus.LOST)
            and state.current_screen is AppScreen.GAME
        ):
            if session.status is GameStatus.WON:
                title = "Победа!"
            elif session.status is GameStatus.LOST:
                title = "Поражение"
            else:
                title = "Результат игры"

            self._game_over_menu_view.set_title(title)

            time_value: int = session.timer_value
            width: int = session.settings.width
            height: int = session.settings.height
            mines: int = session.settings.mine_count
            used_flags: int = session.settings.mine_count - session.remaining_flags

            subtitle_lines = [
                f"Время: {time_value:03} сек",
                f"Поле: {width}×{height}, мин: {mines}",
                f"Флагов поставлено: {used_flags}",
            ]

            self._game_over_menu_view.set_subtitle_lines(subtitle_lines)
            self._app_state_manager.show_game_over()

    def _draw(self) -> None:
        """Отрисовать текущий кадр."""
        surface = self._window
        state = self._app_state_manager.state

        if state.current_screen is AppScreen.MAIN_MENU:
            self._draw_main_menu(surface)
        elif state.current_screen is AppScreen.GAME:
            if state.session is not None:
                self._renderer.draw(surface=surface, session=state.session)
            else:
                self._draw_main_menu(surface)
        elif state.current_screen is AppScreen.PAUSE_MENU:
            if state.session is not None:
                self._renderer.draw(surface=surface, session=state.session)
                self._draw_pause_menu(surface)
            else:
                self._draw_main_menu(surface)
        elif state.current_screen is AppScreen.GAME_OVER:
            if state.session is not None:
                self._renderer.draw(surface=surface, session=state.session)
                self._draw_game_over_menu(surface)
            else:
                self._draw_main_menu(surface)
        else:
            self._draw_placeholder_screen(surface, state.current_screen)

        pygame.display.flip()

    def _draw_main_menu(self, surface: pygame.Surface) -> None:
        """Отрисовать главное меню."""
        bg = self._theme.sprites.get("menu_bg")
        if bg is None:
            surface.fill(self._theme.background_color)
        else:
            bg_scaled = pygame.transform.smoothscale(bg, surface.get_size())
            surface.blit(bg_scaled, (0, 0))

        self._main_menu_view.draw(surface)

    def _draw_pause_menu(self, surface: pygame.Surface) -> None:
        """Отрисовать меню паузы поверх игры."""
        self._pause_menu_view.draw(surface)

    def _draw_game_over_menu(self, surface: pygame.Surface) -> None:
        """Отрисовать меню результата игры поверх поля."""
        self._game_over_menu_view.draw(surface)

    # === Обработка действий меню ===

    def _handle_menu_action(self, action_id: str) -> None:
        """Обработать выбранное действие из меню."""
        if action_id == "new_game_beginner":
            self._start_new_game_with_difficulty(DifficultyLevel.BEGINNER)
        elif action_id == "new_game_intermediate":
            self._start_new_game_with_difficulty(DifficultyLevel.INTERMEDIATE)
        elif action_id == "new_game_expert":
            self._start_new_game_with_difficulty(DifficultyLevel.EXPERT)
        elif action_id == "resume":
            self._app_state_manager.resume_game()
        elif action_id == "restart":
            self._restart_game_with_same_settings()
        elif action_id == "main_menu":
            self._app_state_manager.abort_to_main_menu()
        elif action_id == "settings":
            self._app_state_manager.show_settings()
        elif action_id == "campaign":
            self._app_state_manager.show_campaign_menu()
        elif action_id in ("exit", "quit"):
            self._running = False

    def _get_current_layout(self, session: GameSession) -> LayoutInfo:
        """Получить LayoutInfo для текущего размера окна."""
        layout = self._renderer.calculate_layout(
            surface=self._window,
            board=session.board,
        )
        return layout

    def _start_new_game_with_difficulty(self, difficulty: DifficultyLevel) -> None:
        """Запустить новую игру с указанной сложностью."""
        difficulty_config = DEFAULT_DIFFICULTIES[difficulty]

        session_settings = SessionSettings(
            width=difficulty_config.width,
            height=difficulty_config.height,
            mine_count=difficulty_config.mine_count,
        )
        rules = ClassicMinesweeperRules()

        self._app_state_manager.start_game(
            settings=session_settings,
            rules=rules,
        )

    def _restart_game_with_same_settings(self) -> None:
        """Перезапустить игру с теми же настройками."""
        state = self._app_state_manager.state
        session = state.session
        if session is None:
            return

        settings = session.settings
        rules = ClassicMinesweeperRules()

        new_settings = SessionSettings(
            width=settings.width,
            height=settings.height,
            mine_count=settings.mine_count,
            safe_zone_radius=settings.safe_zone_radius,
            use_question_marks=settings.use_question_marks,
        )

        self._app_state_manager.start_game(
            settings=new_settings,
            rules=rules,
        )

    @staticmethod
    def _draw_placeholder_screen(
        surface: pygame.Surface,
        screen: AppScreen,
    ) -> None:
        """Отрисовать временный экран-заглушку для несделанных меню."""
        surface.fill((32, 32, 32))
        width, height = surface.get_size()

        font = pygame.font.SysFont("consolas", 24)
        text = f"{screen.name} (в разработке)"
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(width // 2, height // 2))
        surface.blit(text_surface, text_rect)
