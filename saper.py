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

        self.cells: list[list[Cell]] = []
        self.cell_containers: list[list[ft.Container]] = []

        self._build_ui()
        self.reset()

    def reset(self):
        """Скидання гри та створення нового поля"""
        self.board_size, self.mines_count = LEVELS[self.level]

        self._build_grid()
        self._set_mines()
        self._calc_mines_around()

        self.page.update()

    def _build_ui(self):
        """Створення інтерфейсу"""
        self.grid_column = ft.Column(
            spacing=1,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.page.add(self.grid_column)

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

    def _on_cell_tap(self, x: int, y: int):
        """Обробка лівого кліку по клітинці"""
        cell = self.cells[x][y]
        if not cell.is_revealed:
            self._reveal_cell(cell)
        self.page.update()

    def _reveal_cell(self, cell: Cell):
        """Розкриття однієї клітинки"""
        if cell.is_revealed or cell.is_flagged:
            return

        cell.is_revealed = True
        self._update_cell_ui(cell)

        if cell.is_mine:
            cell.is_end = True
            self._update_cell_ui(cell)
            return

        if cell.mines_around == 0:
            self._expand_reveal(cell.x, cell.y)

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
        else:
            container.bgcolor = ft.Colors.BLUE_GREY_300
            container.content = None


def main(page: ft.Page):
    MineSweeper(page)


ft.run(main)
