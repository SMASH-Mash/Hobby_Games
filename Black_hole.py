import tkinter as tk
from tkinter import messagebox
import random
import math

class BlackHolePyramidGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Black Hole Pyramid")
        self.root.configure(bg="black")

        self.vs_ai = False
        self.current_player = 1
        self.ai_depth = 2
        self.available_numbers = {1: set(range(1, 11)), 2: set(range(1, 11))}
        self.selected_number = None
        self.buttons = []
        self.board = [None] * 21

        self.neon_cycle = 0
        self.active_panel = None

        self.create_ui()
        self.update_glow()

    def create_ui(self):
        control_frame = tk.Frame(self.root, bg="black")
        control_frame.pack(side=tk.TOP, pady=10)

        rules_btn = tk.Button(control_frame, text="Rules", command=self.show_rules,
                              bg="black", fg="red", activebackground="red", activeforeground="black")
        rules_btn.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(rules_btn, "Show the rules of the game")

        ai_btn = tk.Button(control_frame, text="Toggle vs AI", command=self.toggle_ai,
                           bg="black", fg="red", activebackground="red", activeforeground="black")
        ai_btn.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(ai_btn, "Toggle between 2-player mode and vs AI mode")

        depth_label = tk.Label(control_frame, text="AI Depth:", bg="black", fg="red")
        depth_label.pack(side=tk.LEFT)
        self.depth_slider = tk.Scale(control_frame, from_=1, to=6, orient=tk.HORIZONTAL,
                                     bg="black", fg="red", highlightbackground="black", command=self.set_depth)
        self.depth_slider.set(2)
        self.depth_slider.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(self.depth_slider, "Set how deep the AI searches")

        board_frame = tk.Frame(self.root, bg="black")
        board_frame.pack(pady=20)
        idx = 0
        for row in range(6):
            row_frame = tk.Frame(board_frame, bg="black")
            row_frame.pack()
            for col in range(row+1):
                btn = tk.Button(row_frame, text="", width=4, height=2,
                                command=lambda i=idx: self.place_number(i),
                                bg="black", fg="red", relief=tk.RIDGE)
                btn.grid(row=row, column=col, padx=5, pady=5)
                self.create_tooltip(btn, f"Circle {idx}, click to place your selected number")
                self.buttons.append(btn)
                idx += 1

        self.num_frames = {}
        panel_frame = tk.Frame(self.root, bg="black")
        panel_frame.pack(side=tk.BOTTOM, pady=10)
        for p in [1, 2]:
            f = tk.LabelFrame(panel_frame, text=f"Player {p} Numbers", fg="red", bg="black")
            f.pack(side=tk.LEFT, padx=20)
            self.num_frames[p] = []
            for n in range(1, 11):
                btn = tk.Button(f, text=str(n), command=lambda num=n, player=p: self.select_number(num, player),
                                bg="black", fg="red", width=3)
                btn.grid(row=(n-1)//5, column=(n-1)%5, padx=2, pady=2)
                self.create_tooltip(btn, f"Choose number {n} for Player {p}")
                self.num_frames[p].append(btn)

    def create_tooltip(self, widget, text):
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        label = tk.Label(tooltip, text=text, bg="red", fg="black", relief=tk.SOLID, borderwidth=1)
        label.pack()

        def enter(event):
            tooltip.deiconify()
            x = event.x_root + 10
            y = event.y_root + 10
            tooltip.geometry(f"+{x}+{y}")

        def leave(event):
            tooltip.withdraw()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def update_glow(self):
        self.neon_cycle = (self.neon_cycle + 1) % 20
        glow_color = "#FF0000" if self.current_player == 1 else "#00FF00"
        intensity = 155 + int(100 * abs(math.sin(self.neon_cycle/3)))
        border_color = f"#{intensity:02X}0000" if self.current_player == 1 else f"#00{intensity:02X}00"
        for p in [1, 2]:
            frame = self.num_frames[p][0].master
            if p == self.current_player:
                frame.config(highlightbackground=border_color, highlightcolor=border_color, highlightthickness=3)
            else:
                frame.config(highlightthickness=0)
        self.root.after(100, self.update_glow)

    def select_number(self, num, player):
        if player != self.current_player:
            return
        if num not in self.available_numbers[player]:
            return
        self.selected_number = num

    def place_number(self, idx):
        if self.board[idx] is not None or self.selected_number is None:
            return
        self.board[idx] = (self.current_player, self.selected_number)
        self.buttons[idx].config(text=str(self.selected_number), state=tk.DISABLED)
        # disable number button
        for btn in self.num_frames[self.current_player]:
            if btn["text"] == str(self.selected_number):
                btn.config(state=tk.DISABLED, fg="gray")
        self.available_numbers[self.current_player].remove(self.selected_number)
        self.selected_number = None

        if all(v is not None for v in self.board[:-1]):
            self.finish_game()
            return

        self.current_player = 2 if self.current_player == 1 else 1

        if self.vs_ai and self.current_player == 2:
            self.root.after(500, self.ai_move)

    def ai_move(self):
        if not self.available_numbers[2]:
            return
        idx = random.choice([i for i,v in enumerate(self.board) if v is None])
        num = random.choice(list(self.available_numbers[2]))
        self.selected_number = num
        self.place_number(idx)

    def show_rules(self):
        rules = (
            "1) 2 players place numbers 1-10 into pyramid circles.\n"
            "2) Each number can only be used once per player.\n"
            "3) The last unfilled circle is the Black Hole.\n"
            "4) Each player’s score is the sum of their numbers adjacent to the Black Hole.\n"
            "5) Lower score wins."
        )
        messagebox.showinfo("Rules", rules)

    def toggle_ai(self):
        self.vs_ai = not self.vs_ai
        if self.vs_ai:
            messagebox.showinfo("Mode", "Now playing vs AI")
        else:
            messagebox.showinfo("Mode", "Now in 2-player mode")

    def set_depth(self, val):
        self.ai_depth = int(val)

    def finish_game(self):
        black_hole = self.board.index(None)
        adj = self.get_adjacent(black_hole)
        scores = {1:0, 2:0}
        for i in adj:
            if self.board[i] is not None:
                player, num = self.board[i]
                scores[player] += num
        winner = 1 if scores[1] < scores[2] else 2
        messagebox.showinfo("Game Over", f"Scores: P1={scores[1]}, P2={scores[2]}\nWinner: Player {winner}")

    def get_adjacent(self, idx):
        # approximate adjacency for pyramid
        layer = int((math.sqrt(8*idx+1)-1)//2)
        pos = idx - layer*(layer+1)//2
        neighbors = []
        # upward
        if layer > 0:
            above_start = (layer-1)*layer//2
            neighbors.append(above_start+pos)
            if pos>0:
                neighbors.append(above_start+pos-1)
        # downward
        if layer < 5:
            below_start = (layer+1)*(layer+2)//2 - (layer+1)
            neighbors.append(below_start+pos)
            neighbors.append(below_start+pos+1)
        return [n for n in neighbors if 0<=n<21]

if __name__ == "__main__":
    root = tk.Tk()
    game = BlackHolePyramidGame(root)
    root.mainloop()
