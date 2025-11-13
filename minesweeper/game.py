
from __future__ import annotations
import time
from .board import Board

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
