"""
analytics.py — generate analytics plots for Minesweeper configurations.

Called from the GUI ("Run Analytics...") to produce a SINGLE window
with 4 subplots (2x2 layout):
- White cells histogram
- Number distribution
- Mine cluster distribution
- 3x3 neighborhood heatmap
"""

import numpy as np
import matplotlib.pyplot as plt

# This assumes you are inside the `minesweeper` package.
# If this file sits next to game.py and __init__.py, this is correct:
from .game import MinesweeperGame

MINE = MinesweeperGame.MINE  # e.g. -1


def gen_boards(rows, cols, mines, n=20, seed=None):
    """
    Generate `n` random boards using the game's safe-first-click logic.

    Returns:
        boards: list of 2D lists (board[r][c] is either MINE or 0–8).
    """
    rng = np.random.default_rng(seed)
    boards = []

    for _ in range(n):
        g = MinesweeperGame(rows, cols, mines, safe_first_click=True)
        r = int(rng.integers(0, rows))
        c = int(rng.integers(0, cols))
        g.reveal(r, c)  # triggers mine placement and some reveals
        boards.append([row[:] for row in g.board])

    return boards


def _clusters_single(board):
    """
    Count the number of mine clusters in a single board.
    Mines connected horizontally, vertically OR diagonally are in the same cluster.
    """
    rows = len(board)
    cols = len(board[0])
    visited = set()
    clusters = 0

    for r in range(rows):
        for c in range(cols):
            if board[r][c] == MINE and (r, c) not in visited:
                clusters += 1
                stack = [(r, c)]
                visited.add((r, c))
                while stack:
                    rr, cc = stack.pop()
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = rr + dr, cc + dc
                            if (
                                0 <= nr < rows
                                and 0 <= nc < cols
                                and board[nr][nc] == MINE
                                and (nr, nc) not in visited
                            ):
                                visited.add((nr, nc))
                                stack.append((nr, nc))
    return clusters


def show_all_plots(boards):
    """
    Show ALL four analytics plots together in a single figure (2x2):

    - Top-left: white cells histogram
    - Top-right: number distribution
    - Bottom-left: cluster distribution
    - Bottom-right: avg 3×3 neighborhood mines heatmap
    """
    if not boards:
        return

    boards_arr = np.array(boards)
    n, rows, cols = boards_arr.shape

    # --- Data for white cell counts ---
    white_counts = [
        sum(1 for row in b for v in row if v == 0)
        for b in boards
    ]

    # --- Data for number distribution ---
    values = [v for b in boards for row in b for v in row]

    # --- Data for cluster counts ---
    cluster_counts = [_clusters_single(b) for b in boards]

    # --- Data for heatmap: avg mines in 3×3 neighborhood ---
    mine_masks = (boards_arr == MINE).astype(int)
    heat_accum = np.zeros((rows, cols), dtype=float)

    for b in mine_masks:
        padded = np.pad(b, 1, mode="constant")
        local = np.zeros_like(b)
        for dr in range(3):
            for dc in range(3):
                local += padded[dr:dr + rows, dc:dc + cols]
        heat_accum += local

    avg_heat = heat_accum / n

    # --- Single figure with 4 subplots ---
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))

    # 1) White cells histogram
    ax = axs[0, 0]
    ax.hist(white_counts, bins=20, edgecolor="black")
    ax.set_title("White Cells per Board")
    ax.set_xlabel("Number of white cells")
    ax.set_ylabel("Frequency")

    # 2) Number distribution
    ax = axs[0, 1]
    ax.hist(values, bins=np.arange(-1.5, 9.5, 1), edgecolor="black")
    ax.set_xticks(range(-1, 9))
    ax.set_xticklabels(["M"] + list(range(0, 9)))
    ax.set_title("Distribution of Cell Values")
    ax.set_xlabel("Cell value (M, 0–8)")
    ax.set_ylabel("Count")

    # 3) Cluster distribution
    ax = axs[1, 0]
    if cluster_counts:
        ax.hist(
            cluster_counts,
            bins=range(0, max(cluster_counts) + 2),
            edgecolor="black",
            align="left",
        )
    ax.set_title("Mine Clusters per Board")
    ax.set_xlabel("Number of clusters")
    ax.set_ylabel("Frequency")

    # 4) Heatmap
    ax = axs[1, 1]
    im = ax.imshow(avg_heat, cmap="hot", interpolation="nearest")
    ax.set_title("Avg Mines in 3×3 Neighborhood")
    ax.set_xlabel("Column index")
    ax.set_ylabel("Row index")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Avg mines in 3×3")

    fig.suptitle("Minesweeper Board Analytics", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()
