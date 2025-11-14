
from __future__ import annotations
import time
from board import Board

class Game:
    def __init__(self, board: Board):
        self.board = board
        self.started = False
        self.start_time = None
        self.won = False
        self.lost = False

    @property
    def elapsed(self) -> float:
        if not self.started or self.start_time is None:
            return 0.0
        return max(0.0, time.time() - self.start_time)

    def click(self, r: int, c: int) -> str:
        if not self.started:
            self.board.first_click_place(r, c)
            self.started = True
            self.start_time = time.time()

        result = self.board.reveal(r, c)
        if result == "mine":
            self.lost = True
            return "mine"

        if self.board.count_revealed() == self.board.count_non_mines():
            self.won = True
        return "ok"

    def flag(self, r: int, c: int) -> None:
        self.board.toggle_flag(r, c)


class MinesweeperGame:
    """
    Lightweight game wrapper used by the analytics module.

    It exposes a stable interface that returns the underlying board as a 2D list
    of ints so the analytics code can sample generated layouts without needing
    to know about Board/Cell internals.
    """

    MINE = -1

    def __init__(self, rows: int, cols: int, mines: int, safe_first_click: bool = True):
        self._board = Board(rows, cols, mines, safe_first_click=safe_first_click)
        self._rows = rows
        self._cols = cols
        self._safe_first_click = safe_first_click
        self._started = False

    def reveal(self, r: int, c: int) -> str:
        if not self._started:
            self._board.first_click_place(r, c)
            self._started = True
        return self._board.reveal(r, c)

    @property
    def board(self):
        return [[cell.number for cell in row] for row in self._board.grid]
