
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Iterable, Set
import random

@dataclass
class Cell:
    mine: bool = False
    number: int = 0
    revealed: bool = False
    flagged: bool = False

class Board:
    def __init__(self, rows: int, cols: int, mines: int, safe_first_click: bool = True):
        assert rows > 0 and cols > 0
        assert 0 < mines < rows * cols
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.grid: List[List[Cell]] = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self.safe_first_click = safe_first_click
        self._mines_placed = False  # place mines on first click if safe_first_click True

    def neighbors(self, r: int, c: int) -> Iterable[Tuple[int,int]]:
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

    def _place_mines(self, exclude: Set[Tuple[int,int]] | None = None) -> None:
        exclude = exclude or set()
        positions = [(r,c) for r in range(self.rows) for c in range(self.cols) if (r,c) not in exclude]
        random.shuffle(positions)
        for r,c in positions[:self.mines]:
            self.grid[r][c].mine = True
        # compute numbers
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c].mine: 
                    self.grid[r][c].number = -1
                    continue
                n = 0
                for nr, nc in self.neighbors(r, c):
                    if self.grid[nr][nc].mine: n += 1
                self.grid[r][c].number = n
        self._mines_placed = True

        print("\n[DEBUG] Initial Board Layout (M = mine, numbers = adjacent mine counts):")
        for r in range(self.rows):
            row_repr = []
            for c in range(self.cols):
                cell = self.grid[r][c]
                if cell.mine:
                    row_repr.append("M")
                else:
                    row_repr.append(str(cell.number))
            print(" ".join(row_repr))
        print()

    def first_click_place(self, fr: int, fc: int) -> None:
        if self._mines_placed: return
        if not self.safe_first_click:
            self._place_mines()
            return
        # Only guarantee the first clicked cell is clear; neighbors may contain mines.
        excl = {(fr, fc)}
        self._place_mines(excl)

    def reveal(self, r: int, c: int) -> str:
        cell = self.grid[r][c]
        if cell.revealed or cell.flagged:
            return "ok"
        cell.revealed = True
        if cell.mine:
            return "mine"
        if cell.number == 0:
            stack = [(r, c)]
            seen = set(stack)
            while stack:
                cr, cc = stack.pop()
                for nr, nc in self.neighbors(cr, cc):
                    ncell = self.grid[nr][nc]
                    if (nr,nc) in seen or ncell.flagged: 
                        continue
                    if not ncell.revealed:
                        ncell.revealed = True
                        if not ncell.mine and ncell.number == 0:
                            stack.append((nr,nc))
                            seen.add((nr,nc))
        return "ok"

    def toggle_flag(self, r: int, c: int) -> None:
        cell = self.grid[r][c]
        if cell.revealed: return
        cell.flagged = not cell.flagged

    def count_revealed(self) -> int:
        return sum(1 for r in range(self.rows) for c in range(self.cols) if self.grid[r][c].revealed)

    def count_non_mines(self) -> int:
        return self.rows * self.cols - self.mines
