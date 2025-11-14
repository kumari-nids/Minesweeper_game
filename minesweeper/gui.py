from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess

from board import Board
from game import Game
from config import EASY, INTERMEDIATE, EXPERT, Difficulty
import highscores
import analytics     # <- THIS is important

BOMB = "💣"
FLAG = "🚩"
SMILE = "😊"
DEAD  = "☠️"
COOL  = "😎"

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minesweeper")
        self.resizable(False, False)
        self.theme = "system"
        self.colorblind = False
        self.safe_first_click = True
        self._sys_theme = "light"
        self.withdraw()
        self._show_splash_then_build()

    def _get_system_theme(self) -> str:
        try:
            if self.tk.call('tk', 'windowingsystem') == 'aqua':
                import subprocess
                res = subprocess.run(['defaults','read','-g','AppleInterfaceStyle'], capture_output=True, text=True)
                if res.returncode == 0 and 'Dark' in res.stdout:
                    return 'dark'
                return 'light'
        except Exception:
            pass
        return 'light'

    def _resolved_theme(self) -> str:
        return self._sys_theme if self.theme == 'system' else self.theme

    def _auto_apply_system_theme(self):
        if self.theme != 'system': return
        new_mode = self._get_system_theme()
        if new_mode != getattr(self, '_sys_theme', None):
            self._sys_theme = new_mode
            self._apply_menu_theme()
        try: self.after(1500, self._auto_apply_system_theme)
        except Exception: pass

    def _show_splash_then_build(self):
        w, h = 480, 300
        splash = tk.Toplevel(self)
        self._splash = splash
        splash.overrideredirect(True)
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        x = (sw - w) // 2; y = (sh - h) // 2
        splash.geometry(f"{w}x{h}+{x}+{y}")
        try: splash.attributes("-alpha", 0.0)
        except Exception: pass
        c = tk.Canvas(splash, width=w, height=h, highlightthickness=0, bd=0); c.pack(fill="both", expand=True)
        self._draw_pattern_on_canvas(c, w, h)
        c.create_text(w//2, h//2, text="Minesweeper", font=("Helvetica", 26, "bold"))
        def fade_in(a=0.0):
            try: splash.attributes("-alpha", a)
            except Exception: pass
            if a < 1.0: self.after(30, lambda: fade_in(a+0.08))
            else: self.after(1000, fade_out)
        def fade_out(a=1.0):
            try: splash.attributes("-alpha", a)
            except Exception: pass
            if a > 0.0: self.after(30, lambda: fade_out(a-0.08))
            else: self._end_splash_and_build()
        fade_in()

    def _end_splash_and_build(self):
        try: self._splash.destroy()
        except Exception: pass
        self._sys_theme = self._get_system_theme()
        self.deiconify()
        self._build_menu()
        self._auto_apply_system_theme()

    def _build_menu(self):
        min_w, min_h = 560, 520
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = (sw - min_w) // 2; y = int((sh - min_h) * 0.25)
        self.geometry(f"{min_w}x{min_h}+{x}+{y}")

        self.content_card = tk.Frame(self, padx=24, pady=22)
        self.content_card.place(relx=0.5, rely=0.50, anchor="center")
        self.title_label = tk.Label(self.content_card, text="Minesweeper", font=("Helvetica", 24, "bold"))
        self.title_label.pack(pady=(0, 18))

        self._menu_buttons = []
        def add_btn(text, cmd, top=8):
            b = tk.Button(self.content_card, text=text, width=28, command=cmd)
            b.pack(pady=(top, 8))
            self._menu_buttons.append(b)

        add_btn("Easy",           lambda: self._start(EASY), top=0)
        add_btn("Intermediate",   lambda: self._start(INTERMEDIATE))
        add_btn("Expert",         lambda: self._start(EXPERT))
        add_btn("Custom",         self._start_custom)
        add_btn("High Scores",    self._show_highscores_dialog, top=14)
        add_btn("Run Analytics…", self._run_analytics_info)

        self.settings_icon = tk.Label(self, text="⚙️", cursor="hand2")
        self.quit_icon = tk.Label(self, text="✖️", cursor="hand2")
        self.settings_icon.place(relx=0.02, rely=0.98, anchor="sw")
        self.quit_icon.place(relx=0.98, rely=0.98, anchor="se")
        self.settings_icon.bind("<Button-1>", lambda e: self._open_settings())
        self.quit_icon.bind("<Button-1>", lambda e: self.destroy())

        self._apply_menu_theme()

    def _draw_pattern_on_canvas(self, canvas, w, h):
        items = ["1","2","3","4","5","6","7","8", BOMB, FLAG]
        colors = {"1":"#1976d2","2":"#388e3c","3":"#d32f2f","4":"#7b1fa2",
                  "5":"#5d4037","6":"#00838f","7":"#000000","8":"#616161"}
        safe_cx, safe_cy = w//2, h//2
        safe_w, safe_h = 300, 90
        idx = 0
        for iy in range(24, h, 32):
            for ix in range(24, w, 32):
                if (safe_cx - safe_w//2) <= ix <= (safe_cx + safe_w//2) and (safe_cy - safe_h//2) <= iy <= (safe_cy + safe_h//2):
                    continue
                t = items[idx % len(items)]; idx += 1
                if t in colors:
                    canvas.create_text(ix, iy, text=t, font=("Helvetica", 12, "bold"), fill=colors[t])
                else:
                    canvas.create_text(ix, iy, text=t, font=("Helvetica", 14))

    def _menu_palette(self):
        mode = self._resolved_theme()
        if mode == "dark":
            return {"bg":"#808080","card_bg":"#a9a9a9","title_fg":"#000000",
                    "btn_bg":"#cfcfcf","btn_fg":"#000000","btn_active":"#dedede","icon_fg":"#000000"}
        else:
            return {"bg":"#f2f2f2","card_bg":"#ffffff","title_fg":"#202020",
                    "btn_bg":"#ffffff","btn_fg":"#202020","btn_active":"#f0f0f0","icon_fg":"#202020"}

    def _apply_menu_theme(self):
        pal = self._menu_palette()
        self.configure(bg=pal["bg"])
        self.content_card.configure(bg=pal["card_bg"])
        self.title_label.configure(bg=pal["card_bg"], fg=pal["title_fg"])
        for b in getattr(self, "_menu_buttons", []):
            b.configure(bg=pal["btn_bg"], activebackground=pal["btn_active"], fg=pal["btn_fg"])
        self.settings_icon.configure(bg=pal["bg"], fg=pal["icon_fg"])
        self.quit_icon.configure(bg=pal["bg"], fg=pal["icon_fg"])

    # ----- Settings & extras -----
    def _open_settings(self):
        win = tk.Toplevel(self)
        win.title("Settings")
        win.resizable(False, False)
        frm = tk.Frame(win, padx=12, pady=12); frm.pack(fill="both", expand=True)

        tk.Label(frm, text="Theme").grid(row=0, column=0, sticky="w")
        theme_var = tk.StringVar(value=self.theme)
        for i, name in enumerate(["light", "dark", "system"]):
            tk.Radiobutton(frm, text=name.title(), variable=theme_var, value=name).grid(row=0, column=1+i, sticky="w")

        cb_var = tk.BooleanVar(value=self.colorblind)
        tk.Label(frm, text="Colorblind palette").grid(row=1, column=0, sticky="w")
        tk.Checkbutton(frm, variable=cb_var, text="Enable").grid(row=1, column=1, sticky="w")

        sfc_var = tk.BooleanVar(value=self.safe_first_click)
        tk.Label(frm, text="Safe-first-click").grid(row=2, column=0, sticky="w")
        tk.Checkbutton(frm, variable=sfc_var, text="Enable").grid(row=2, column=1, sticky="w")

        btns = tk.Frame(frm); btns.grid(row=3, column=0, columnspan=4, pady=(10,0), sticky="e")
        def apply_and_close():
            self.theme = theme_var.get()
            self.colorblind = cb_var.get()
            self.safe_first_click = bool(sfc_var.get())
            if self.theme == "system":
                self._sys_theme = self._get_system_theme()
            self._apply_menu_theme()
            self._auto_apply_system_theme()
            win.destroy()
        tk.Button(btns, text="Cancel", command=win.destroy).pack(side="right", padx=6)
        tk.Button(btns, text="Apply", command=apply_and_close).pack(side="right")

    def _start(self, diff):
        self.withdraw()
        game = MinesweeperWindow(self, diff.rows, diff.cols, diff.mines,
                                 theme=self._resolved_theme(),
                                 colorblind=self.colorblind,
                                 safe_first_click=self.safe_first_click)
        game.protocol("WM_DELETE_WINDOW", lambda: (game.destroy(), self.deiconify()))
        game.mainloop()

    def _prompt_custom_board(self, title="Custom Board"):
        rows = simpledialog.askinteger(
            title, "Rows (5-500):", parent=self, minvalue=5, maxvalue=500
        )
        if rows is None:
            return None

        cols = simpledialog.askinteger(
            title, "Columns (5-500):", parent=self, minvalue=5, maxvalue=500
        )
        if cols is None:
            return None

        max_mines = rows * cols - 1
        if max_mines <= 0:
            messagebox.showerror(title, "Board is too small for mines.", parent=self)
            return None

        mines = simpledialog.askinteger(
            title,
            f"Mines (1-{max_mines}):",
            parent=self,
            minvalue=1,
            maxvalue=max_mines,
        )
        if mines is None:
            return None

        return Difficulty(rows, cols, mines)

    def _start_custom(self):
        diff = self._prompt_custom_board("Custom Board")
        if diff:
            self._start(diff)

    def _show_highscores_dialog(self):
        choice = simpledialog.askstring("High Scores", "Enter one: easy, intermediate, expert")
        if not choice: return
        diff = {"easy": EASY, "intermediate": INTERMEDIATE, "expert": EXPERT}.get(choice.strip().lower())
        if not diff:
            tk.messagebox.showerror("High Scores", "Invalid choice."); return
        rows, cols, mines = diff.rows, diff.cols, diff.mines
        top = highscores.get_top10(rows, cols, mines)
        if not top:
            tk.messagebox.showinfo("High Scores", f"No highscores for {rows}x{cols} with {mines} mines yet."); return
        lines = [f"Top 10 for {rows}x{cols} with {mines} mines:\n"]
        for i, s in enumerate(top, 1):
            lines.append(f"{i:2d}. {s['name']:<12} {s['time']:.2f}s  ({s['when']})")
        tk.messagebox.showinfo("High Scores", "\n".join(lines))

    def _run_analytics_info(self):
        """
        GUI entry for analytics:
        - Ask user for difficulty (Easy / Intermediate / Expert / Custom)
        - Ask user for number of boards
        - Generate boards and show ALL plots in one window.
        """
        # Choose difficulty for analytics
        choice = simpledialog.askstring(
            "Analytics Difficulty",
            "Enter difficulty for analytics:\n"
            "easy / intermediate / expert / custom",
            parent=self,
        )
        if not choice:
            return

        choice = choice.strip().lower()
        if choice.startswith("e") and "asy" in choice:
            diff = EASY
        elif choice.startswith("i"):
            diff = INTERMEDIATE
        elif choice.startswith("e") and "xpert" in choice:
            diff = EXPERT
        elif choice.startswith("c"):
            diff = self._prompt_custom_board("Analytics Custom Board")
            if not diff:
                return
        else:
            messagebox.showerror(
                "Error",
                "Invalid difficulty. Use: easy / intermediate / expert / custom.",
                parent=self,
            )
            return

        # Number of random boards
        n = simpledialog.askinteger(
            "Analytics",
            "How many random boards to generate?",
            parent=self,
            minvalue=5,
            maxvalue=500,
        )
        if not n:
            return

        rows, cols, mines = diff.rows, diff.cols, diff.mines

        # Generate boards & show all plots in a single figure
        boards = analytics.gen_boards(rows, cols, mines, n)
        if not boards:
            messagebox.showinfo("Analytics", "No boards generated.", parent=self)
            return

        analytics.show_all_plots(boards)



class Tile(tk.Frame):
    def __init__(self, master, pal, size=26):
        super().__init__(master, bd=0, highlightthickness=0, bg=pal["board_bg"], width=size, height=size)
        self.pal = pal
        self.pack_propagate(False); self.grid_propagate(False)
        self._build()

    def _build(self):
        outer = tk.Frame(self, bd=0, highlightthickness=0, bg=self.pal["tile_unrev_bg"])
        outer.pack(fill="both", expand=True)
        outer.grid_propagate(False)
        outer.rowconfigure(1, weight=1); outer.columnconfigure(1, weight=1)

        self.top    = tk.Frame(outer, height=2, bg=self.pal["edge_light"]); self.top.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.left   = tk.Frame(outer, width=2,  bg=self.pal["edge_light"]); self.left.grid(row=1, column=0, sticky="ns")
        self.right  = tk.Frame(outer, width=2,  bg=self.pal["edge_dark"]);  self.right.grid(row=1, column=2, sticky="ns")
        self.bottom = tk.Frame(outer, height=2, bg=self.pal["edge_dark"]);  self.bottom.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.center = tk.Frame(outer, bg=self.pal["tile_unrev_bg"], bd=0, highlightthickness=0)
        self.center.grid(row=1, column=1, sticky="nsew")
        self.label  = tk.Label(self.center, text=" ", bg=self.pal["tile_unrev_bg"], fg=self.pal["tile_fg"])
        self.label.pack(expand=True)

    def set_raised(self):
        self.top.config(bg=self.pal["edge_light"]); self.left.config(bg=self.pal["edge_light"])
        self.right.config(bg=self.pal["edge_dark"]); self.bottom.config(bg=self.pal["edge_dark"])
        self.center.config(bg=self.pal["tile_unrev_bg"]); self.label.config(bg=self.pal["tile_unrev_bg"])

    def set_pressed(self):
        self.top.config(bg=self.pal["edge_dark"]); self.left.config(bg=self.pal["edge_dark"])
        self.right.config(bg=self.pal["edge_light"]); self.bottom.config(bg=self.pal["edge_light"])
        self.center.config(bg=self.pal["tile_rev_bg"]); self.label.config(bg=self.pal["tile_rev_bg"])

    def set_revealed_base(self):
        self.top.config(bg=self.pal["tile_rev_bg"]); self.left.config(bg=self.pal["tile_rev_bg"])
        self.right.config(bg=self.pal["tile_rev_bg"]); self.bottom.config(bg=self.pal["tile_rev_bg"])
        self.center.config(bg=self.pal["tile_rev_bg"]); self.label.config(bg=self.pal["tile_rev_bg"])

    def set_text(self, text, fg=None):
        self.label.config(text=text, fg=(fg or self.pal["tile_fg"]))

    def set_flag(self, fg=None):
        self.set_raised(); self.set_text(FLAG, (fg or self.pal["flag_fg"]))

    def set_mine(self, fg=None):
        self.set_revealed_base(); self.set_text(BOMB, (fg or self.pal["mine_fg"]))

class MinesweeperWindow(tk.Toplevel):
    def __init__(self, parent, rows, cols, mines, theme='system', colorblind=False, safe_first_click=True):
        super().__init__(parent)
        self.parent = parent
        self.title("Minesweeper")
        self.rows, self.cols, self.mines = rows, cols, mines
        self.theme = theme
        self.colorblind = colorblind
        self.safe_first_click = safe_first_click
        self._build_ui(); self._apply_theme(); self._new_game()
        self.bind_all("<ButtonPress-1>", lambda e: (not (self.game.won or self.game.lost)) and self.face_var.set("😮"))
        self.bind_all("<ButtonRelease-1>", lambda e: (not (self.game.won or self.game.lost)) and self.face_var.set(SMILE))

    def _build_ui(self):
        top = tk.Frame(self, padx=8, pady=8); top.pack(fill="x")
        self.mines_left_var = tk.StringVar(value="Mines: 0")
        self.face_var = tk.StringVar(value=SMILE)
        self.timer_var = tk.StringVar(value="Time: 0.00s")
        tk.Label(top, textvariable=self.mines_left_var, font=("Helvetica", 12)).pack(side="left")
        tk.Button(top, textvariable=self.face_var, font=("Helvetica", 14), width=3, command=self._restart).pack(side="left", expand=True)
        tk.Label(top, textvariable=self.timer_var, font=("Helvetica", 12)).pack(side="right")

        self.board_frame = tk.Frame(self, padx=8, pady=8); self.board_frame.pack()
        bottom = tk.Frame(self, padx=8, pady=8); bottom.pack(fill="x")
        tk.Button(bottom, text="⬅️", width=2, command=self._back_to_menu).pack(side="right")

    def _get_theme_palette(self):
        if self.theme == 'dark':
            return {"bg":"#808080","board_bg":"#808080","tile_unrev_bg":"#c0c0c0","tile_unrev_hover":"#d0d0d0",
                    "tile_rev_bg":"#e0e0e0","tile_fg":"#000000","flag_fg":"#d32f2f","mine_fg":"#000000",
                    "edge_light":"#ffffff","edge_dark":"#7b7b7b"}
        else:
            return {"bg":"#f2f2f2","board_bg":"#eaeaea","tile_unrev_bg":"#fafafa","tile_unrev_hover":"#f0f0f0",
                    "tile_rev_bg":"#e6e6e6","tile_fg":"#000000","flag_fg":"#c62828","mine_fg":"#000000",
                    "edge_light":"#ffffff","edge_dark":"#c2c2c2"}

    def _apply_theme(self):
        pal = self._get_theme_palette()
        self.configure(bg=pal["bg"]); self.board_frame.configure(bg=pal["board_bg"])
        if hasattr(self, "tiles"):
            for (r,c), t in self.tiles.items():
                t.pal = pal
                cell = self.game.board.grid[r][c]
                if cell.revealed: t.set_revealed_base()
                elif cell.flagged: t.set_flag()
                else: t.set_raised()

    def _restart(self): self._new_game()
    def _back_to_menu(self): self.destroy(); self.parent.deiconify()

    def _new_game(self):
        for w in self.board_frame.winfo_children(): w.destroy()
        self.face_var.set(SMILE)
        self.game = Game(Board(self.rows, self.cols, self.mines, safe_first_click=self.safe_first_click))
        self.tiles = {}
        pal = self._get_theme_palette()
        tile_size = 26
        for r in range(self.rows): self.board_frame.rowconfigure(r, minsize=tile_size)
        for c in range(self.cols): self.board_frame.columnconfigure(c, minsize=tile_size)

        for r in range(self.rows):
            for c in range(self.cols):
                t = Tile(self.board_frame, pal, size=tile_size); t.grid(row=r, column=c)
                for w in (t, t.center, t.label):
                    w.bind("<ButtonPress-1>", lambda e, rr=r, cc=c: self._press(rr, cc))
                    w.bind("<ButtonRelease-1>", lambda e, rr=r, cc=c: self._release_left(rr, cc))
                    w.bind("<Leave>", lambda e, rr=r, cc=c: self._leave(rr, cc))
                    w.bind("<Enter>", lambda e, rr=r, cc=c: self._hover_on(rr, cc))
                    w.bind("<Button-2>", lambda e, rr=r, cc=c: self._on_right(rr, cc))
                    w.bind("<Button-3>", lambda e, rr=r, cc=c: self._on_right(rr, cc))
                t.set_raised(); self.tiles[(r,c)] = t
        self._update_mines_left(); self._tick()

    def _hover_on(self, r, c):
        cell = self.game.board.grid[r][c]
        if not cell.revealed and not cell.flagged:
            pal = self._get_theme_palette()
            t = self.tiles.get((r,c))
            if t: t.center.config(bg=pal["tile_unrev_hover"]); t.label.config(bg=pal["tile_unrev_hover"])

    def _press(self, r, c):
        if self.game.won or self.game.lost: return
        cell = self.game.board.grid[r][c]
        if not cell.revealed and not cell.flagged:
            t = self.tiles.get((r,c)); 
            if t: t.set_pressed()

    def _leave(self, r, c):
        cell = self.game.board.grid[r][c]
        if not cell.revealed and not cell.flagged:
            pal = self._get_theme_palette()
            t = self.tiles.get((r,c))
            if t:
                t.set_raised()
                t.center.config(bg=pal["tile_unrev_bg"]); t.label.config(bg=pal["tile_unrev_bg"])

    def _release_left(self, r, c):
        if self.game.won or self.game.lost: return
        self._on_left(r, c)

    def _tick(self):
        if self.game.won: self.face_var.set(COOL)
        elif self.game.lost: self.face_var.set(DEAD)
        self.timer_var.set(f"Time: {self.game.elapsed:.2f}s")
        if not (self.game.won or self.game.lost): self.after(100, self._tick)

    def _update_mines_left(self):
        flags = sum(1 for r in range(self.rows) for c in range(self.cols) if self.game.board.grid[r][c].flagged)
        self.mines_left_var.set(f"Mines: {max(0, self.mines - flags)}")

    def _on_left(self, r, c):
        if self.game.won or self.game.lost: return
        result = self.game.click(r, c); self._refresh()
        if result == "mine":
            self._reveal_all(); self.face_var.set(DEAD); messagebox.showinfo("Game Over", "Boom! You clicked on a mine.")
        elif self.game.won:
            self._reveal_all(); self.face_var.set(COOL)
            name = simpledialog.askstring("You won!", "Enter your name for highscores:")
            if name: highscores.submit_score(self.rows, self.cols, self.mines, name, self.game.elapsed)
            messagebox.showinfo("Congratulations", f"You cleared the board in {self.game.elapsed:.2f} seconds!")

    def _on_right(self, r, c):
        if self.game.won or self.game.lost: return
        self.game.flag(r, c); self._update_mines_left(); self._refresh()

    def _num_color(self, n):
        if getattr(self, "colorblind", False):
            palette = {1:"#00429d",2:"#2a788e",3:"#22a884",4:"#7ad151",5:"#fde725",6:"#5e3c99",7:"#e66101",8:"#b2abd2"}
        else:
            palette = {1:"#1976d2",2:"#388e3c",3:"#d32f2f",4:"#7b1fa2",5:"#5d4037",6:"#00838f",7:"#000000",8:"#616161"}
        return palette.get(n, "#000000")

    def _refresh(self):
        pal = self._get_theme_palette()
        for (r,c), t in self.tiles.items():
            cell = self.game.board.grid[r][c]
            if cell.revealed:
                t.set_revealed_base()
                if cell.mine: t.set_text(BOMB, pal["mine_fg"])
                else:
                    if cell.number > 0: t.set_text(str(cell.number), self._num_color(cell.number))
                    else: t.set_text(" ", pal["tile_fg"])
            else:
                if cell.flagged: t.set_flag(pal["flag_fg"])
                else:
                    t.set_raised(); t.set_text(" ", pal["tile_fg"])

    def _reveal_all(self):
        pal = self._get_theme_palette()
        for (r,c), t in self.tiles.items():
            cell = self.game.board.grid[r][c]
            t.set_revealed_base()
            if cell.mine: t.set_text(BOMB, pal["mine_fg"])
            elif cell.number == 0: t.set_text(" ", pal["tile_fg"])
            else: t.set_text(str(cell.number), self._num_color(cell.number))

def run_gui(rows: int, cols: int, mines: int, safe_first_click: bool = True):
    app = Launcher(); app.mainloop()
