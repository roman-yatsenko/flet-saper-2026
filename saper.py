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
        self._build_grid()
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

                row_containers.append(container)
                row.controls.append(container)

            self.cells.append(row_cells)
            self.cell_containers.append(row_containers)
            self.grid_column.controls.append(row)


def main(page: ft.Page):
    MineSweeper(page)


ft.run(main)
