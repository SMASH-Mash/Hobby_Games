import tkinter as tk
from tkinter import messagebox

class SudokuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver (Dark Red Theme)")
        self.entries = [[None for _ in range(9)] for _ in range(9)]
        self.delay = 100  # ms delay for visualization
        self.paused = False
        self.stop_visual = False
        self.create_styles()
        self.create_grid()
        self.create_buttons()

    def create_styles(self):
        self.bg_color = "#1c1c1c"   # dark background
        self.cell_bg = "#2a2a2a"    # cell background
        self.text_color = "#ff4c4c" # red hue for text
        self.btn_bg = "#333333"
        self.btn_fg = "#ff6666"

        self.root.configure(bg=self.bg_color)

    def create_grid(self):
        frame = tk.Frame(self.root, bg=self.bg_color)
        frame.pack(padx=20, pady=20)
        for r in range(9):
            for c in range(9):
                e = tk.Entry(frame, width=3, font=("Consolas", 20, "bold"),
                             justify="center", bg=self.cell_bg, fg=self.text_color,
                             insertbackground=self.text_color, relief="solid")
                e.grid(row=r, column=c, padx=2, pady=2, ipady=8)
                if r % 3 == 0 and r != 0:
                    e.grid(pady=(10, 2))
                if c % 3 == 0 and c != 0:
                    e.grid(padx=(10, 2))
                self.entries[r][c] = e

    def create_buttons(self):
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(pady=10)

        def make_btn(txt, cmd):
            return tk.Button(btn_frame, text=txt, command=cmd, width=14,
                             bg=self.btn_bg, fg=self.btn_fg, activebackground="#550000",
                             activeforeground="white", font=("Arial", 12, "bold"))

        make_btn("Validate", self.validate).grid(row=0, column=0, padx=5)
        make_btn("Solve Instantly", self.solve).grid(row=0, column=1, padx=5)
        make_btn("Solve Step-by-Step", self.solve_visual).grid(row=0, column=2, padx=5)
        make_btn("Pause/Resume", self.toggle_pause).grid(row=0, column=3, padx=5)
        make_btn("Clear", self.clear).grid(row=0, column=4, padx=5)
        make_btn("Load Sample", self.load_sample).grid(row=0, column=5, padx=5)

    def read_board(self):
        board = []
        for r in range(9):
            row = []
            for c in range(9):
                val = self.entries[r][c].get().strip()
                if val == "" or val == "0" or val == ".":
                    row.append(0)
                else:
                    try:
                        row.append(int(val))
                    except:
                        row.append(0)
            board.append(row)
        return board

    def write_board(self, board):
        for r in range(9):
            for c in range(9):
                self.entries[r][c].delete(0, tk.END)
                if board[r][c] != 0:
                    self.entries[r][c].insert(0, str(board[r][c]))

    def validate(self):
        board = self.read_board()
        conflicts = self.find_conflicts(board)
        if conflicts:
            messagebox.showerror("Validation Failed", "\n".join(conflicts))
        else:
            messagebox.showinfo("Validation", "No conflicts found. Grid looks valid.")

    def find_conflicts(self, b):
        conflicts = []
        for r in range(9):
            seen = {}
            for c in range(9):
                v = b[r][c]
                if v == 0: continue
                if v in seen:
                    conflicts.append(f"Row {r+1} has duplicate {v}")
                else:
                    seen[v] = True
        for c in range(9):
            seen = {}
            for r in range(9):
                v = b[r][c]
                if v == 0: continue
                if v in seen:
                    conflicts.append(f"Column {c+1} has duplicate {v}")
                else:
                    seen[v] = True
        for br in range(3):
            for bc in range(3):
                seen = {}
                for r in range(3):
                    for c in range(3):
                        R, C = br*3+r, bc*3+c
                        v = b[R][C]
                        if v == 0: continue
                        if v in seen:
                            conflicts.append(f"Box {br*3+bc+1} has duplicate {v}")
                        else:
                            seen[v] = True
        return conflicts

    def solve(self):
        board = self.read_board()
        conflicts = self.find_conflicts(board)
        if conflicts:
            messagebox.showerror("Cannot Solve", "\n".join(conflicts))
            return
        if self.backtrack(board):
            self.write_board(board)
            messagebox.showinfo("Solved", "Sudoku solved successfully!")
        else:
            messagebox.showerror("Unsolvable", "No solution exists for this grid.")

    def backtrack(self, b):
        empty = self.find_empty(b)
        if not empty:
            return True
        r, c = empty
        for num in range(1, 10):
            if self.is_safe(b, r, c, num):
                b[r][c] = num
                if self.backtrack(b):
                    return True
                b[r][c] = 0
        return False

    def solve_visual(self):
        board = self.read_board()
        conflicts = self.find_conflicts(board)
        if conflicts:
            messagebox.showerror("Cannot Solve", "\n".join(conflicts))
            return
        self.stop_visual = False
        self.paused = False
        self.visual_backtrack(board)

    def visual_backtrack(self, b):
        if self.stop_visual:
            return False
        empty = self.find_empty(b)
        if not empty:
            messagebox.showinfo("Solved", "Sudoku solved successfully!")
            return True
        r, c = empty
        for num in range(1, 10):
            if self.is_safe(b, r, c, num):
                b[r][c] = num
                self.entries[r][c].delete(0, tk.END)
                self.entries[r][c].insert(0, str(num))
                self.root.update()
                self.wait_if_paused()
                self.root.after(self.delay)
                if self.visual_backtrack(b):
                    return True
                b[r][c] = 0
                self.entries[r][c].delete(0, tk.END)
                self.root.update()
                self.wait_if_paused()
                self.root.after(self.delay)
        return False

    def wait_if_paused(self):
        while self.paused:
            self.root.update()

    def toggle_pause(self):
        self.paused = not self.paused

    def find_empty(self, b):
        for r in range(9):
            for c in range(9):
                if b[r][c] == 0:
                    return (r, c)
        return None

    def is_safe(self, b, r, c, num):
        if any(b[r][i] == num for i in range(9)): return False
        if any(b[i][c] == num for i in range(9)): return False
        br, bc = r//3*3, c//3*3
        for i in range(3):
            for j in range(3):
                if b[br+i][bc+j] == num: return False
        return True

    def clear(self):
        for r in range(9):
            for c in range(9):
                self.entries[r][c].delete(0, tk.END)

    def load_sample(self):
        sample = [
            [5,3,0,0,7,0,0,0,0],
            [6,0,0,1,9,5,0,0,0],
            [0,9,8,0,0,0,0,6,0],
            [8,0,0,0,6,0,0,0,3],
            [4,0,0,8,0,3,0,0,1],
            [7,0,0,0,2,0,0,0,6],
            [0,6,0,0,0,0,2,8,0],
            [0,0,0,4,1,9,0,0,5],
            [0,0,0,0,8,0,0,7,9]
        ]
        self.write_board(sample)


if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuApp(root)
    root.mainloop()
