
from dataclasses import dataclass

@dataclass(frozen=True)
class Difficulty:
    rows: int
    cols: int
    mines: int

EASY         = Difficulty(9, 9, 10)
INTERMEDIATE = Difficulty(16, 16, 40)
EXPERT       = Difficulty(16, 30, 99)
