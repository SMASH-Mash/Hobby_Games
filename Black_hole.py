import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import time
import copy

# Pyramid layers (21 positions)
layers = [[0], [1, 2], [3, 4, 5], [6, 7, 8, 9], [10, 11, 12, 13, 14], [15, 16, 17, 18, 19, 20]]

# Precompute adjacency
adjacency = {i: set() for i in range(21)}
for row in range(len(layers)):
    for idx, node in enumerate(layers[row]):
        if idx > 0:
            adjacency[node].add(layers[row][idx-1])
        if idx < len(layers[row]) - 1:
            adjacency[node].add(layers[row][idx+1])
        if row+1 < len(layers):
            adjacency[node].add(layers[row+1][idx])
            adjacency[node].add(layers[row+1][idx+1])
        if row-1 >= 0 and idx < len(layers[row-1]):
            adjacency[node].add(layers[row-1][idx])
        if row-1 >= 0 and idx-1 >= 0:
            adjacency[node].add(layers[row-1][idx-1])

# Utility: higher is better for AI (AI wants opponent_score - ai_score high because lower own score wins)

def terminal_utility(board, ai_name="AI", opp_name="Player"):
    # compute black hole
    if board.count(None) != 1:
        return None
    black = board.index(None)
    scores = {ai_name: 0, opp_name: 0}
    for adj in adjacency[black]:
        if board[adj] is not None:
            val, owner = board[adj]
            if owner == ai_name:
                scores[ai_name] += val
            else:
                scores[opp_name] += val
    # utility positive if opponent_score - ai_score positive
    return scores[opp_name] - scores[ai_name]


def heuristic(board, ai_name="AI", opp_name="Player"):
    # Simple heuristic: for each empty cell, compute opponent_adj - ai_adj using current placements
    empties = [i for i, v in enumerate(board) if v is None]
    if not empties:
        return 0
    vals = []
    for e in empties:
        ai_sum = 0
        opp_sum = 0
        for adj in adjacency[e]:
            if board[adj] is not None:
                val, owner = board[adj]
                if owner == ai_name:
                    ai_sum += val
                else:
                    opp_sum += val
        vals.append(opp_sum - ai_sum)
    # AI assumes opponent will try to maximize their advantage — pessimistic for AI, take max
    # But since AI wants higher opp - ai (good for AI), we return the average as estimated value
    return sum(vals) / len(vals)


class Tooltip:
    def __init__(self, widget):
        self.widget = widget
        self.tip = None
    def show(self, text, x, y):
        if self.tip:
            self.hide()
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tip, text=text, bg="#111", fg="#ff4444", bd=1, relief=tk.SOLID, padx=4, pady=2, font=("Consolas", 10))
        label.pack()
    def hide(self):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class BlackHoleGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Black Hole Pyramid")
        self.canvas = tk.Canvas(root, width=700, height=560, bg="#000")
        self.canvas.pack()

        # Controls
        ctrl = tk.Frame(root, bg="#000")
        ctrl.pack(fill=tk.X)
        self.rules_btn = tk.Button(ctrl, text="Rules", command=self.show_rules, bg="#111", fg="#ff4444")
        self.rules_btn.pack(side=tk.LEFT, padx=8, pady=6)
        self.rules_btn.bind("<Enter>", lambda e: self.show_tooltip(self.rules_btn, "Show game rules"))
        self.rules_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        self.ai_btn = tk.Button(ctrl, text="Toggle vs AI", command=self.toggle_ai, bg="#111", fg="#ff4444")
        self.ai_btn.pack(side=tk.LEFT, padx=8)
        self.ai_btn.bind("<Enter>", lambda e: self.show_tooltip(self.ai_btn, "Play single player vs AI"))
        self.ai_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        tk.Label(ctrl, text="AI Depth:", bg="#000", fg="#ff4444").pack(side=tk.LEFT, padx=8)
        self.depth_var = tk.IntVar(value=3)
        self.depth_scale = tk.Scale(ctrl, from_=1, to=6, orient=tk.HORIZONTAL, variable=self.depth_var, bg="#000", fg="#ff4444", highlightthickness=0)
        self.depth_scale.pack(side=tk.LEFT)
        self.depth_scale.bind("<Enter>", lambda e: self.show_tooltip(self.depth_scale, "Search depth for AI (higher = stronger but slower)"))
        self.depth_scale.bind("<Leave>", lambda e: self.hide_tooltip())

        self.restart_btn = tk.Button(ctrl, text="Restart", command=self.restart, bg="#111", fg="#ff4444")
        self.restart_btn.pack(side=tk.RIGHT, padx=8)
        self.restart_btn.bind("<Enter>", lambda e: self.show_tooltip(self.restart_btn, "Restart the game"))
        self.restart_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        # Game state
        self.board = [None] * 21
        self.players = ["Player", "AI"]
        self.turn = 0
        self.vs_ai = False

        # Draw circles
        self.positions = {}
        self.texts = {}
        self.tooltip = Tooltip(self.canvas)
        self.draw_board()

    def draw_board(self):
        radius = 26
        for row, nodes in enumerate(layers):
            y = 70 + row * 80
            start_x = 350 - (len(nodes) - 1) * 50
            for i, node in enumerate(nodes):
                x = start_x + i * 100
                circle = self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill="#060606", outline="#ff4444", width=3)
                text = self.canvas.create_text(x, y, text="", fill="#00ff99", font=("Consolas", 12, "bold"))
                self.positions[node] = (circle, text, x, y)
                self.canvas.tag_bind(circle, "<Button-1>", lambda e, n=node: self.handle_click(n))
                self.canvas.tag_bind(circle, "<Enter>", lambda e, n=node: self.on_hover(n))
                self.canvas.tag_bind(circle, "<Leave>", lambda e: self.hide_tooltip())

    def on_hover(self, node):
        circ, txt, x, y = self.positions[node]
        status = "Empty" if self.board[node] is None else f"{self.board[node][1]}:{self.board[node][0]}"
        self.show_tooltip(self.canvas, f"Pos {node} - {status}", x+10, y+10)

    def show_tooltip(self, widget, text, x=None, y=None):
        if isinstance(widget, tk.Scale):
            x = widget.winfo_rootx() + 10
            y = widget.winfo_rooty() + 30
        elif hasattr(widget, 'winfo_rootx'):
            x = widget.winfo_rootx() + 10
            y = widget.winfo_rooty() + 30
        if x is None:
            x = 100
            y = 100
        self.tooltip.show(text, x, y)

    def hide_tooltip(self):
        self.tooltip.hide()

    def handle_click(self, node):
        if self.board[node] is not None:
            return
        current_player = self.players[self.turn % 2]
        if self.vs_ai and current_player == "AI":
            return
        # Ask for number via dialog
        try:
            val = simpledialog.askinteger("Choose Number", f"{current_player}, enter a number (1-10):", minvalue=1, maxvalue=10)
        except:
            val = None
        if val is None:
            return
        self.make_move(node, val, current_player)
        if self.vs_ai and self.board.count(None) > 1:
            self.root.after(200, self.make_ai_move)

    def make_move(self, node, val, player):
        self.board[node] = (val, player)
        circle, text, x, y = self.positions[node]
        color_fill = "#0d0d0d"
        outline = "#00ff99" if player == "Player" else "#ff4444"
        text_color = "#00ff99" if player == "Player" else "#ff4444"
        self.canvas.itemconfig(circle, fill=color_fill, outline=outline)
        self.canvas.itemconfig(text, text=str(val), fill=text_color)
        self.turn += 1
        if self.board.count(None) == 1:
            self.end_game()

    def restart(self):
        self.board = [None] * 21
        self.turn = 0
        for node in range(21):
            circle, text, x, y = self.positions[node]
            self.canvas.itemconfig(circle, fill="#060606", outline="#ff4444")
            self.canvas.itemconfig(text, text="")

    def toggle_ai(self):
        self.vs_ai = not self.vs_ai
        mode = "Single Player vs AI" if self.vs_ai else "Two Player"
        messagebox.showinfo("Mode", f"Now playing: {mode}")
        # reset names
        self.players = ["Player", "AI"] if self.vs_ai else ["Player", "Player 2"]

    def make_ai_move(self):
        depth = self.depth_var.get()
        # Run minimax to choose best move for AI
        best_val = -float('inf')
        best_move = None
        start = time.time()
        empties = [i for i, v in enumerate(self.board) if v is None]
        # iterate all possible moves (position, number)
        for pos in empties:
            for num in range(1, 11):
                bcopy = copy.deepcopy(self.board)
                bcopy[pos] = (num, "AI")
                val = self.alphabeta(bcopy, depth-1, False, -float('inf'), float('inf'))
                if val is None:
                    continue
                if val > best_val:
                    best_val = val
                    best_move = (pos, num)
        if best_move is None:
            # fallback random
            available = [i for i, v in enumerate(self.board) if v is None]
            pos = random.choice(available)
            num = random.randint(1, 10)
        else:
            pos, num = best_move
        # Apply move
        self.make_move(pos, num, "AI")

    def alphabeta(self, board_state, depth, maximizing, alpha, beta):
        # Check terminal
        util = terminal_utility(board_state, ai_name="AI", opp_name="Player")
        if util is not None:
            return util
        if depth == 0:
            return heuristic(board_state, ai_name="AI", opp_name="Player")
        empties = [i for i, v in enumerate(board_state) if v is None]
        if maximizing:
            value = -float('inf')
            # AI's turn to place
            for pos in empties:
                for num in range(1, 11):
                    board_state[pos] = (num, "AI")
                    val = self.alphabeta(board_state, depth-1, False, alpha, beta)
                    board_state[pos] = None
                    if val is None:
                        continue
                    if val > value:
                        value = val
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        return value
            return value
        else:
            # Opponent (Player) will try to maximize their utility (opp - ai), which is same objective as AI
            value = float('inf')
            for pos in empties:
                for num in range(1, 11):
                    board_state[pos] = (num, "Player")
                    val = self.alphabeta(board_state, depth-1, True, alpha, beta)
                    board_state[pos] = None
                    if val is None:
                        continue
                    if val < value:
                        value = val
                    beta = min(beta, value)
                    if alpha >= beta:
                        return value
            return value

    def end_game(self):
        black_hole = self.board.index(None)
        scores = {"AI": 0, "Player": 0, "Player 2": 0}
        for adj in adjacency[black_hole]:
            if self.board[adj] is not None:
                val, owner = self.board[adj]
                scores[owner] = scores.get(owner, 0) + val

        msg = f"Black hole at {black_hole}\n"
        if self.vs_ai:
            msg += f"Your score: {scores.get('Player',0)}\n"
            msg += f"AI score: {scores.get('AI',0)}\n"
            if scores.get('Player',0) < scores.get('AI',0):
                msg += "You win!"
            elif scores.get('AI',0) < scores.get('Player',0):
                msg += "AI wins!"
            else:
                msg += "It's a tie!"
        else:
            msg += f"Player 1 score: {scores.get('Player',0)}\n"
            msg += f"Player 2 score: {scores.get('Player 2',0)}\n"
            if scores.get('Player',0) < scores.get('Player 2',0):
                msg += "Player 1 wins!"
            elif scores.get('Player 2',0) < scores.get('Player',0):
                msg += "Player 2 wins!"
            else:
                msg += "It's a tie!"

        messagebox.showinfo("Game Over", msg)

    def show_rules(self):
        rules = (
            "Rules:\n"
            "1. Two players take turns placing numbers (1-10) in circles.\n"
            "2. The pyramid has 21 circles arranged in 6 layers.\n"
            "3. One circle remains empty at the end — the Black Hole.\n"
            "4. Each player's score = sum of their numbers next to the Black Hole.\n"
            "5. The lower score wins.\n"
            "\nAI specifics:\n"
            "- Toggle 'Toggle vs AI' to play against the computer.\n"
            "- Use the AI Depth slider to select search depth (higher = stronger but slower)."
        )
        messagebox.showinfo("Rules", rules)


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="#000")
    game = BlackHoleGame(root)
    root.mainloop()