from tkinter import CENTER

import flet as ft
import random
import time

# Рівні складності: (розмір поля, кількість мін)
LEVELS = (
    (8, 10),
    (16, 40),
    {24, 99},
)

# Статуси гри
STATUS_READY = 0
STATUS_PLAY = 1
STATUS_FAILED = 2
STATUS_SUCCESS = 3

# Емодзі для кнопки статусу
STATUS_EMOJIS = {
    STATUS_READY: "🟢",
    STATUS_PLAY: "😊",
    STATUS_FAILED: "💀",
    STATUS_SUCCESS: "😎",
}

# Кольори цифр (кількість мін навколо клітинки)
NUM_COLORS = {
    1: ft.Colors.BLUE,
    2: ft.Colors.GREEN_800,
    3: ft.Colors.RED,
    4: ft.Colors.INDIGO,
    5: ft.Colors.BROWN_700,
    6: ft.Colors.TEAL,
    7: ft.Colors.BLACK,
    8: ft.Colors.GREY_600,
}

CELL_SIZE = 30


class Cell:
    """Стан однієї клітинки ігрового поля"""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.reset()

    def reset(self):
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.is_start = False
        self.is_end = False
        self.mines_around = 0


class MineSweeper:
    """Головний клас застосунку Сапер"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Сапер"
        self.page.padding = 10
        self.page.scroll = ft.ScrollMode.AUTO

        self.level = 0
        self.board_size, self.mines_count = LEVELS[self.level]
        self.remaining_mines = self.mines_count
        self.status = STATUS_READY
        self.timer_start = 0
        self.timer_running = False

        self.cells: list[list[Cell]] = []
        self.cell_containers: list[list[ft.Container]] = []

        self._build_ui()
        self.reset()

    def reset(self):
        """Скидання гри та створення нового поля"""
        self.board_size, self.mines_count = LEVELS[self.level]
        self.remaining_mines = self.mines_count
        self.status = STATUS_READY
        self.timer_start = 0
        self.timer_running = False

        self.mines_label.value = f"{self.remaining_mines:03d}"
        self.timer_label.value = "000"
        self.status_emoji.value = STATUS_EMOJIS[STATUS_READY]

        self._build_grid()
        self._set_mines()
        self._calc_mines_around()
        self._set_start()

        self.page.update()

    def _build_ui(self):
        """Створення інтерфейсу"""
        # Лічильник мін
        self.mines_label = ft.Text(
            f"{self.mines_count:03d}",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.RED_700,
            font_family="Consolas",
        )

        # Кнопка статусу / перезапуску
        self.status_emoji = ft.Text(STATUS_EMOJIS[STATUS_READY], size=24)
        self.status_button = ft.Container(
            content=self.status_emoji,
            width=50,
            height=50,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1, ft.Colors.GREY_500),
            border_radius=5,
            bgcolor=ft.Colors.BLUE_GREY_100,
            on_click=self._on_status_button_click,
        )

        # Таймер
        self.timer_label = ft.Text(
            "000",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.RED_700,
            font_family="Consolas",
        )

        self.level_dropdown = ft.Dropdown(
            width=200,
            value="0",
            options=[
                ft.dropdown.Option("0", "Легкий 8x8"),
                ft.dropdown.Option("1", "Середній 16x16"),
                ft.dropdown.Option("2", "Складний 24x24"),
            ],
            on_select=self._on_level_change,
        )

        toolbar = ft.Row(
            [
                ft.Text("💣", size=24),
                self.mines_label,
                ft.Container(expand=True),
                self.status_button,
                ft.Container(expand=True),
                self.timer_label,
                ft.Text("⏱️", size=24),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        level_row = ft.Row(
            [self.level_dropdown],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.grid_column = ft.Column(
            spacing=1,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.page.add(toolbar, level_row, self.grid_column)

    def _build_grid(self):
        """Побудова ігрового поля"""
        self.cells = []
        self.cell_containers = []
        self.grid_column.controls.clear()

        for x in range(self.board_size):
            row_cells = []
            row_containers = []
            row = ft.Row(spacing=1, alignment=ft.MainAxisAlignment.CENTER)

            for y in range(self.board_size):
                cell = Cell(x, y)
                row_cells.append(cell)

                container = ft.Container(
                    width=CELL_SIZE,
                    height=CELL_SIZE,
                    bgcolor=ft.Colors.BLUE_GREY_300,
                    border_radius=2,
                    border=ft.Border.all(1, ft.Colors.GREY_500),
                    alignment=ft.Alignment.CENTER,
                )

                gesture = ft.GestureDetector(
                    content=container,
                    on_tap=lambda e, cx=x, cy=y: self._on_cell_tap(cx, cy),
                    on_secondary_tap=lambda e, cx=x, cy=y: self._on_cell_secondary(
                        cx, cy
                    ),
                    on_long_press_start=lambda e, cx=x, cy=y: self._on_cell_secondary(
                        cx, cy
                    ),
                )

                row_containers.append(container)
                row.controls.append(gesture)

            self.cells.append(row_cells)
            self.cell_containers.append(row_containers)
            self.grid_column.controls.append(row)

    def _calc_mines_around(self):
        """Обчислення кількості мін навколо кожної клітинки"""
        for x, y, cell in self._get_all_cells():
            if not cell.is_mine:
                cell.mines_around = sum(
                    1 for _, _, c in self._get_neighbors(x, y) if c.is_mine
                )
                # self.cell_containers[x][y].content = ft.Text(str(cell.mines_around))

    def _check_win(self):
        """Перевірка умови перемоги."""
        if self.status != STATUS_PLAY:
            return

        # Варіант 1: всі міни позначені прапорцями, решта розкрита
        if self.remaining_mines == 0:
            if all(
                cell.is_revealed or cell.is_flagged
                for _, _, cell in self._get_all_cells()
            ):
                self._update_status(STATUS_SUCCESS)
                self.timer_running = False
                return

        # Варіант 2: залишились тільки нерозкриті клітинки з мінами
        unrevealed = []
        for _, _, cell in self._get_all_cells():
            if not cell.is_revealed and not cell.is_flagged:
                unrevealed.append(cell)
                if len(unrevealed) > self.mines_count or not cell.is_mine:
                    return

        if len(unrevealed) == self.mines_count:
            for cell in unrevealed:
                cell.is_flagged = True
                self._update_cell_ui(cell)
            self.remaining_mines = 0
            self.mines_label.value = "000"
            self._update_status(STATUS_SUCCESS)
            self.timer_running = False

    def _collect_chord_cells(self, x, y, to_reveal, visited):
        """Рекурсивний збір клітинок для chord-розкриття."""
        base_cell = self.cells[x][y]
        flagged_count = sum(int(c.is_flagged) for _, _, c in self._get_neighbors(x, y))
        if flagged_count == base_cell.mines_around and base_cell.mines_around > 0:
            for xi, yi, cell in self._get_neighbors(x, y):
                if (
                    not cell.is_flagged
                    and not cell.is_revealed
                    and (xi, yi) not in visited
                ):
                    visited.add((xi, yi))
                    to_reveal.append((xi, yi, cell))
                    if not cell.is_mine:
                        self._collect_chord_cells(xi, yi, to_reveal, visited)

    def _expand_reveal(self, x: int, y: int):
        """Рокриття порожніх клітинок методом заливки (BFS)"""
        queue = [(x, y)]
        while queue:
            cx, cy = queue.pop(0)
            for xi, yi, cell in self._get_neighbors(cx, cy):
                if not cell.is_mine and not cell.is_flagged and not cell.is_revealed:
                    cell.is_revealed = True
                    self._update_cell_ui(cell)
                    if cell.mines_around == 0:
                        queue.append((xi, yi))

    def _game_over(self):
        """Обробка програшу."""
        self._update_status(STATUS_FAILED)
        self.timer_running = False
        self._reveal_grid()

    def _get_all_cells(self):
        """Генератор всіх клітинок поля"""
        for x in range(self.board_size):
            for y in range(self.board_size):
                yield x, y, self.cells[x][y]

    def _get_neighbors(self, x: int, y: int):
        """Отримати список сусідніх клітинок (до 8 штук)"""
        result = []
        for xi in range(max(0, x - 1), min(x + 2, self.board_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.board_size)):
                if xi != x or yi != y:
                    result.append((xi, yi, self.cells[xi][yi]))
        return result

    def _handle_chord(self, x: int, y: int):
        """Розкриття сусідів при правильній кількості прапорців."""
        to_reveal = []
        visited = set()
        self._collect_chord_cells(x, y, to_reveal, visited)
        for _, _, cell in to_reveal:
            self._reveal_cell(cell)

    def _on_cell_secondary(self, x: int, y: int):
        """Обробка правого кліку / довгого натискання."""
        if self.status in (STATUS_FAILED, STATUS_SUCCESS):
            return

        if self.status == STATUS_READY:
            self._start_game()

        cell = self.cells[x][y]
        if not cell.is_revealed:
            cell.is_flagged = not cell.is_flagged
            self.remaining_mines += -1 if cell.is_flagged else 1
            self.mines_label.value = f"{self.remaining_mines:03d}"
            self._update_cell_ui(cell)
        else:
            self._handle_chord(x, y)

        self._check_win()
        self.page.update()

    def _on_cell_tap(self, x: int, y: int):
        """Обробка лівого кліку по клітинці"""
        if self.status in (STATUS_FAILED, STATUS_SUCCESS):
            return

        if self.status == STATUS_READY:
            self._start_game()

        cell = self.cells[x][y]
        if not cell.is_revealed:
            self._reveal_cell(cell)
        else:
            self._handle_chord(x, y)

        self._check_win()
        self.page.update()

    def _on_level_change(self, e):
        """Обробка зміни рівня складності."""
        self.level = int(e.control.value)
        self.reset()

    def _on_status_button_click(self, e):
        """Обробка кліку по кнопці статусу."""
        if self.status == STATUS_PLAY:
            # Під час гри: здатись
            self._update_status(STATUS_FAILED)
            self.timer_running = False
            self._reveal_grid()
            self.page.update()
        elif self.status in (STATUS_FAILED, STATUS_SUCCESS):
            # Після завершення гри: нова гра
            self.reset()

    def _reveal_cell(self, cell: Cell):
        """Розкриття однієї клітинки"""
        if cell.is_revealed or cell.is_flagged:
            return

        cell.is_revealed = True
        self._update_cell_ui(cell)

        if cell.is_mine:
            cell.is_end = True
            self._update_cell_ui(cell)
            self._game_over()
            return

        if cell.mines_around == 0:
            self._expand_reveal(cell.x, cell.y)

    def _reveal_grid(self):
        """Розкриття всього поля (при програші)."""
        for _, _, cell in self._get_all_cells():
            if not (cell.is_flagged and cell.is_mine):
                cell.is_revealed = True
                self._update_cell_ui(cell)

    def _set_mines(self):
        """Випадкове розміщення мін на полі"""
        positions = set()
        while len(positions) < self.mines_count:
            x = random.randint(0, self.board_size - 1)
            y = random.randint(0, self.board_size - 1)
            if (x, y) not in positions:
                self.cells[x][y].is_mine = True
                # self.cell_containers[x][y].content = ft.Text("💣")
                positions.add((x, y))

    def _set_start(self):
        """Вибір стартової клітинки та розкриття її околу."""
        empty_cells = [
            cell
            for x, y, cell in self._get_all_cells()
            if (
                not cell.is_mine
                and cell.mines_around == 0
                and (
                    x == 0
                    or y == 0
                    or x == self.board_size - 1
                    or y == self.board_size - 1
                )
            )
        ]
        if not empty_cells:
            return

        start_cell = random.choice(empty_cells)
        start_cell.is_start = True
        self._reveal_cell(start_cell)

    def _start_game(self):
        """Початок гри: запуск таймера"""
        self._update_status(STATUS_PLAY)
        self.timer_start = int(time.time())
        self.timer_running = True
        self.page.run_task(self._timer_tick)

    async def _timer_tick(self):
        """Оновлення таймера кожну секунду"""
        import asyncio

        while self.timer_running and self.status == STATUS_PLAY:
            n_seconds = int(time.time()) - self.timer_start
            self.timer_label.value = f"{n_seconds:03d}"
            self.page.update()
            await asyncio.sleep(1)

    def _update_cell_ui(self, cell: Cell):
        """Оновлення відображення клітинки"""
        container = self.cell_containers[cell.x][cell.y]

        if cell.is_revealed:
            if cell.is_end:
                container.bgcolor = ft.Colors.RED_400
                container.content = ft.Text("💣", size=14)
            elif cell.is_mine:
                container.bgcolor = ft.Colors.GREY_300
                container.content = ft.Text("💣", size=14)
            elif cell.is_start:
                container.bgcolor = ft.Colors.GREY_200
                container.content = ft.Text("🚀", size=14)
            elif cell.mines_around > 0:
                container.bgcolor = ft.Colors.GREY_200
                container.content = ft.Text(
                    str(cell.mines_around),
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=NUM_COLORS.get(cell.mines_around, ft.Colors.BLACK),
                )
            else:
                container.bgcolor = ft.Colors.GREY_200
                container.content = None
        elif cell.is_flagged:
            container.bgcolor = ft.Colors.BLUE_GREY_300
            container.content = ft.Text("🚩", size=14)
        else:
            container.bgcolor = ft.Colors.BLUE_GREY_300
            container.content = None

    def _update_status(self, status: int):
        """Оновлення статусу гри."""
        self.status = status
        self.status_emoji.value = STATUS_EMOJIS[status]


def main(page: ft.Page):
    MineSweeper(page)


ft.run(main)
