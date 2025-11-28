"""Логика игрового поля Сапёра.

Содержит описание одной клетки (Tile) и класса Board, который управляет
расположением мин, подсчётом чисел и открытием клеток (включая flood fill).

Модуль не зависит от pygame и может использоваться отдельно от визуализации.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import List, Optional, Set, Tuple

from .enums import TileContent, TileState
from .results import BoardUpdateResult
from .settings import (
    MAX_MINES_FACTOR,
    MIN_BOARD_HEIGHT,
    MIN_BOARD_WIDTH,
    MIN_MINES,
)


class BoardConfigurationError(ValueError):
    """Исключение, выбрасываемое при некорректных параметрах поля."""


class BoardCoordinatesError(ValueError):
    """Исключение, выбрасываемое при обращении к клетке вне поля."""


@dataclass(slots=True)
class Tile:
    """Клетка игрового поля.

    Attributes:
        is_mine:
            True, если клетка содержит мину.
        state:
            Текущее состояние клетки (скрыта, открыта, флаг и т.п.).
        adjacent_mines:
            Количество мин в соседних клетках (0–8).
        content:
            Тип содержимого клетки (пустая, число, мина, особое).
        tags:
            Набор произвольных тегов для будущих расширений
            (например, бонусы, щиты и другие модовые механики).
    """

    is_mine: bool = False
    state: TileState = TileState.HIDDEN
    adjacent_mines: int = 0
    content: TileContent = TileContent.EMPTY
    tags: Optional[Set[str]] = field(default=None)


class Board:
    """Игровое поле Сапёра.

    Класс отвечает за:
        * хранение состояния всех клеток;
        * расстановку мин с учётом безопасной зоны первого клика;
        * подсчёт количества соседних мин;
        * открытие клеток (включая flood fill);
        * установку и снятие флажков/вопросительных знаков;
        * проверку условия победы.

    Координаты клеток задаются в системе (x, y), где:
        x — столбец [0, width - 1],
        y — строка [0, height - 1].
    """

    def __init__(
        self,
        width: int,
        height: int,
        mine_count: int,
        safe_zone_radius: int,
        use_question_marks: bool,
        random_generator: Optional[Random] = None,
    ) -> None:
        """Создать новое поле."""
        self._validate_dimensions(width=width, height=height, mine_count=mine_count)

        if safe_zone_radius < 0:
            raise BoardConfigurationError(
                "safe_zone_radius не может быть отрицательным.",
            )

        self.width: int = width
        self.height: int = height
        self.mine_count: int = mine_count
        self.safe_zone_radius: int = safe_zone_radius
        self.use_question_marks: bool = use_question_marks

        self._tiles: List[List[Tile]] = [
            [Tile() for _ in range(width)] for _ in range(height)
        ]

        self._random: Random = random_generator or Random()
        self._mines_generated: bool = False

    @staticmethod
    def _validate_dimensions(width: int, height: int, mine_count: int) -> None:
        """Проверить корректность размеров поля и количества мин."""
        if width < MIN_BOARD_WIDTH:
            raise BoardConfigurationError(
                f"Ширина поля слишком мала: {width}. "
                f"Минимально допустимая ширина: {MIN_BOARD_WIDTH}.",
            )

        if height < MIN_BOARD_HEIGHT:
            raise BoardConfigurationError(
                f"Высота поля слишком мала: {height}. "
                f"Минимально допустимая высота: {MIN_BOARD_HEIGHT}.",
            )

        cell_count = width * height
        if cell_count <= 0:
            raise BoardConfigurationError(
                "Количество клеток на поле должно быть положительным.",
            )

        if mine_count < MIN_MINES:
            raise BoardConfigurationError(
                f"Слишком мало мин: {mine_count}. "
                f"Минимальное количество мин: {MIN_MINES}.",
            )

        max_mines_by_factor = int(cell_count * MAX_MINES_FACTOR)
        if max_mines_by_factor < MIN_MINES:
            max_mines_by_factor = MIN_MINES

        if mine_count >= cell_count:
            raise BoardConfigurationError(
                "Количество мин не может быть больше или равно количеству клеток.",
            )

        if mine_count > max_mines_by_factor:
            raise BoardConfigurationError(
                f"Слишком много мин: {mine_count}. "
                f"Максимально допустимое количество мин при текущем размере поля: "
                f"{max_mines_by_factor}.",
            )

    def in_bounds(self, x: int, y: int) -> bool:
        """Проверить, лежат ли координаты внутри поля."""
        return 0 <= x < self.width and 0 <= y < self.height

    def _require_in_bounds(self, x: int, y: int) -> None:
        """Убедиться, что координаты клетки находятся внутри поля."""
        if not self.in_bounds(x=x, y=y):
            raise BoardCoordinatesError(
                f"Координаты ({x}, {y}) находятся вне поля размером "
                f"{self.width}×{self.height}.",
            )

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Получить список координат соседних клеток (8 направлений)."""
        neighbors: List[Tuple[int, int]] = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = x + dx
                ny = y + dy
                if self.in_bounds(x=nx, y=ny):
                    neighbors.append((nx, ny))
        return neighbors

    def _reset_tiles(self) -> None:
        """Сбросить состояние всех клеток до начального."""
        for row in self._tiles:
            for tile in row:
                tile.is_mine = False
                tile.state = TileState.HIDDEN
                tile.adjacent_mines = 0
                tile.content = TileContent.EMPTY
                tile.tags = None

    def _is_in_safe_zone(self, x: int, y: int, safe_x: int, safe_y: int) -> bool:
        """Проверить, попадает ли клетка в безопасную зонy первого клика."""
        dx = abs(x - safe_x)
        dy = abs(y - safe_y)
        return max(dx, dy) <= self.safe_zone_radius

    def place_mines(self, safe_x: int, safe_y: int) -> None:
        """Расставить мины на поле с учётом безопасной зоны."""
        self._require_in_bounds(x=safe_x, y=safe_y)
        self._reset_tiles()

        all_positions: List[Tuple[int, int]] = []
        for y in range(self.height):
            for x in range(self.width):
                if not self._is_in_safe_zone(x=x, y=y, safe_x=safe_x, safe_y=safe_y):
                    all_positions.append((x, y))

        if len(all_positions) < self.mine_count:
            raise BoardConfigurationError(
                "Невозможно разместить все мины вне безопасной зоны. "
                "Уменьшите радиус безопасной зоны или число мин.",
            )

        self._random.shuffle(all_positions)
        mine_positions = all_positions[: self.mine_count]

        for x, y in mine_positions:
            tile = self._tiles[y][x]
            tile.is_mine = True
            tile.content = TileContent.MINE

        self._recalculate_adjacent_mines()
        self._mines_generated = True

    def _recalculate_adjacent_mines(self) -> None:
        """Пересчитать количество соседних мин для всех клеток."""
        for y in range(self.height):
            for x in range(self.width):
                tile = self._tiles[y][x]
                if tile.is_mine:
                    tile.adjacent_mines = 0
                    tile.content = TileContent.MINE
                    continue

                mines_around = 0
                for nx, ny in self.get_neighbors(x=x, y=y):
                    if self._tiles[ny][nx].is_mine:
                        mines_around += 1

                tile.adjacent_mines = mines_around
                if mines_around == 0:
                    tile.content = TileContent.EMPTY
                else:
                    tile.content = TileContent.NUMBER

    def get_tile(self, x: int, y: int) -> Tile:
        """Получить клетку по координатам."""
        self._require_in_bounds(x=x, y=y)
        return self._tiles[y][x]

    # --- Геттеры, которые использует UI/renderer ---

    def get_tile_state(self, x: int, y: int) -> TileState:
        """Получить состояние клетки (для рендера и HUD)."""
        return self.get_tile(x=x, y=y).state

    def get_adjacent_mines(self, x: int, y: int) -> int:
        """Получить количество соседних мин для клетки."""
        return self.get_tile(x=x, y=y).adjacent_mines

    def is_mine(self, x: int, y: int) -> bool:
        """Проверить, есть ли мина в указанной клетке."""
        return self.get_tile(x=x, y=y).is_mine

    # --- Игровые действия ---

    def open_tile(
        self,
        x: int,
        y: int,
        *,
        safe_first_click: bool = True,
    ) -> BoardUpdateResult:
        """Открыть клетку по указанным координатам."""
        self._require_in_bounds(x=x, y=y)

        if not self._mines_generated and safe_first_click:
            self.place_mines(safe_x=x, safe_y=y)

        changed: List[Tuple[int, int]] = []
        tile = self._tiles[y][x]

        if tile.state == TileState.REVEALED:
            return BoardUpdateResult(changed=changed, exploded=False, won=self.is_win())

        if tile.is_mine:
            tile.state = TileState.REVEALED
            changed.append((x, y))
            return BoardUpdateResult(changed=changed, exploded=True, won=False)

        # Открываем безопасную клетку.
        if tile.adjacent_mines == 0:
            self._flood_reveal(x=x, y=y, changed=changed)
        else:
            tile.state = TileState.REVEALED
            changed.append((x, y))

        won = self.is_win()
        return BoardUpdateResult(changed=changed, exploded=False, won=won)

    def _flood_reveal(self, x: int, y: int, changed: List[Tuple[int, int]]) -> None:
        """Рекурсивно (через очередь) открыть пустые клетки и их границу."""
        queue: List[Tuple[int, int]] = [(x, y)]
        while queue:
            cx, cy = queue.pop()
            tile = self._tiles[cy][cx]

            if tile.state == TileState.REVEALED:
                continue
            if tile.state in (TileState.FLAGGED, TileState.QUESTION):
                # Не раскрываем клетки, помеченные игроком.
                continue
            if tile.is_mine:
                continue

            tile.state = TileState.REVEALED
            changed.append((cx, cy))

            if tile.adjacent_mines != 0:
                continue

            for nx, ny in self.get_neighbors(x=cx, y=cy):
                neighbor = self._tiles[ny][nx]
                if neighbor.state == TileState.HIDDEN:
                    queue.append((nx, ny))

    def toggle_flag(self, x: int, y: int) -> int:
        """Переключить состояние пометки клетки (флаг/вопрос/пусто)."""
        self._require_in_bounds(x=x, y=y)
        tile = self._tiles[y][x]

        if tile.state == TileState.REVEALED:
            return 0

        if tile.state == TileState.HIDDEN:
            tile.state = TileState.FLAGGED
            return 1

        if tile.state == TileState.FLAGGED:
            if self.use_question_marks:
                tile.state = TileState.QUESTION
                return -1
            tile.state = TileState.HIDDEN
            return -1

        if tile.state == TileState.QUESTION:
            tile.state = TileState.HIDDEN
            return 0

        return 0

    def is_win(self) -> bool:
        """Проверить, выполнено ли условие победы."""
        for row in self._tiles:
            for tile in row:
                if not tile.is_mine and tile.state != TileState.REVEALED:
                    return False
        return True
