import math
import sys
import pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN, KEYDOWN, K_r, K_u

"""
Neon Tic-Tac-Toe (adjustable grid) with Alpha-Beta pruning
----------------------------------------------------------
- Left click to place your mark (Player X by default).
- Press R to restart, U to undo last human move (if allowed).
- Change BOARD_N to adjust grid size (e.g., 3..5 works well).
- WIN_LENGTH can be <= BOARD_N; default is BOARD_N (N-in-a-row).

Notes
-----
For N > 3, game-tree size grows quickly. Alpha-beta + a simple
heuristic keeps it playable up to around 5x5 on most machines.
"""

# ============================
# Tweakables
# ============================
BOARD_N = 5        # Grid size (e.g., 3 for 3x3, 4 for 4x4)
WIN_LENGTH = None  # If None, equals BOARD_N; otherwise set e.g. 3, 4, 5
HUMAN_PLAYS = 'X'  # 'X' or 'O'
AI_PLAYS    = 'O' if HUMAN_PLAYS == 'X' else 'X'
WINDOW_SIZE = 720  # Square window
MARGIN = 24        # Outer margin
PANEL_WIDTH = 220  # Width of the side panel where buttons live
LINE_THICKNESS = 4
FPS = 60

# Neon palette
BG_COLOR = (8, 10, 20)
NEON_GRID = (0, 255, 200)
NEON_X = (255, 70, 130)
NEON_O = (50, 150, 255)
GLOW_STEPS = 8  # quality/speed tradeoff

# Search limits (for larger boards)
MAX_SEARCH_TIME_MS = 1200  # soft limit; not strictly enforced in this basic version
MAX_DEPTH = 3  # cap depth for larger boards if needed

# ============================
# Core game state
# ============================
WIN_LENGTH = BOARD_N if WIN_LENGTH is None else WIN_LENGTH

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption(f"Neon Tic-Tac-Toe {BOARD_N}x{BOARD_N}")
font = pygame.font.SysFont("Montserrat", 28)
small_font = pygame.font.SysFont("Montserrat", 20)

# New: dynamic fields initialized in prepare_game()

def prepare_game():
    global CELL_SIZE, GRID_ORIGIN, BOARD_AREA, PANEL_RECT, EMPTY, board, move_history, current_player
    # Compute cell size leaving room for side panel
    available_width = WINDOW_SIZE - 2 * MARGIN - PANEL_WIDTH
    CELL_SIZE = available_width // BOARD_N
    board_pixel_size = CELL_SIZE * BOARD_N
    GRID_ORIGIN = (MARGIN, (WINDOW_SIZE - board_pixel_size) // 2)
    BOARD_AREA = pygame.Rect(GRID_ORIGIN[0], GRID_ORIGIN[1], board_pixel_size, board_pixel_size)
    PANEL_RECT = pygame.Rect(WINDOW_SIZE - MARGIN - PANEL_WIDTH, MARGIN, PANEL_WIDTH, WINDOW_SIZE - 2*MARGIN)
    EMPTY = '.'
    board = [[EMPTY for _ in range(BOARD_N)] for __ in range(BOARD_N)]
    move_history = []
    current_player = 'X'


# UI helpers for settings & help
def draw_button(surf, rect, text, active=True):
    color_bg = (30, 40, 60) if active else (20, 25, 35)
    pygame.draw.rect(surf, color_bg, rect, border_radius=6)
    pygame.draw.rect(surf, NEON_GRID, rect, 2, border_radius=6)
    txt = small_font.render(text, True, (220, 230, 255))
    txt_r = txt.get_rect(center=rect.center)
    surf.blit(txt, txt_r)


def point_in_rect(pos, rect):
    x, y = pos
    return rect.left <= x <= rect.right and rect.top <= y <= rect.bottom


def draw_label_value(surf, label, value_text, centerx, y):
    lbl = small_font.render(label, True, (180, 200, 230))
    val = font.render(value_text, True, (240, 250, 255))
    lbl_r = lbl.get_rect(center=(centerx, y))
    val_r = val.get_rect(center=(centerx, y + 30))
    surf.blit(lbl, lbl_r)
    surf.blit(val, val_r)


def help_screen():
    # Simple overlay with rules and close button
    running_help = True
    lines = [
        "Neon Tic-Tac-Toe — Help",
        "",
        "Left click to place your mark.",
        "Press R to restart current game. Press U to undo last human move (if allowed).",
        "Use the settings screen to choose:",
        " - Board Size: number of rows/columns (N x N)",
        " - Your Mark: choose X or O (if you choose O then AI starts)",
        " - AI Max Depth: limits how deep the AI searches (higher = stronger/slower)",
        " - Win Length: how many in a row are needed to win (use 'Auto' = board size)",
        "",
        "For N > 3 the game tree grows quickly; adjust AI Max Depth to keep UI responsive.",
        "",
        "Click 'Back' or press R to return to the game."
    ]
    while running_help:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                pygame.quit()
                sys.exit()
            elif ev.type == KEYDOWN:
                if ev.key == K_r:
                    running_help = False
            elif ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                # back button area
                back_rect = pygame.Rect((WINDOW_SIZE//2 - 70, WINDOW_SIZE - 90, 140, 44))
                if point_in_rect((mx, my), back_rect):
                    running_help = False

        screen.fill((6, 8, 14,))
        # Panel
        panel = pygame.Rect(60, 60, WINDOW_SIZE - 120, WINDOW_SIZE - 140)
        pygame.draw.rect(screen, (10, 15, 30), panel, border_radius=8)
        pygame.draw.rect(screen, NEON_GRID, panel, 2, border_radius=8)

        # Draw lines
        start_y = 100
        for i, line in enumerate(lines):
            txt = small_font.render(line, True, (200, 220, 240))
            screen.blit(txt, (panel.left + 24, start_y + i * 28))

        # Back button
        back_rect = pygame.Rect((WINDOW_SIZE//2 - 70, WINDOW_SIZE - 90, 140, 44))
        draw_button(screen, back_rect, "Back")

        pygame.display.flip()
        clock.tick(FPS)


def settings_screen():
    global BOARD_N, HUMAN_PLAYS, AI_PLAYS, MAX_DEPTH, WIN_LENGTH
    # Local editable copies
    b_n = BOARD_N
    h_play = HUMAN_PLAYS
    max_d = MAX_DEPTH
    win_l = WIN_LENGTH if WIN_LENGTH is not None else b_n

    start_rect = pygame.Rect((WINDOW_SIZE//2 - 120, WINDOW_SIZE - 140, 110, 48))
    help_rect = pygame.Rect((WINDOW_SIZE//2 + 10, WINDOW_SIZE - 140, 110, 48))

    # controls positions
    centerx = WINDOW_SIZE // 2
    opts = [
        ("Board Size (N)", lambda: str(b_n)),
        ("Your Mark", lambda: h_play),
        ("AI Max Depth", lambda: str(max_d)),
        ("Win Length", lambda: ("Auto" if win_l == b_n else str(win_l))),
    ]

    # arrow button rectangles (we'll build them dynamically per item)
    running_settings = True
    while running_settings:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                pygame.quit()
                sys.exit()
            elif ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                # Start / Help
                if point_in_rect((mx, my), start_rect):
                    # Apply selections to globals
                    BOARD_N = max(3, min(9, int(b_n)))
                    HUMAN_PLAYS = 'X' if h_play == 'X' else 'O'
                    AI_PLAYS = 'O' if HUMAN_PLAYS == 'X' else 'X'
                    MAX_DEPTH = max(1, min(12, int(max_d)))
                    WIN_LENGTH = BOARD_N if (int(win_l) == BOARD_N) else int(win_l)
                    running_settings = False
                    break
                if point_in_rect((mx, my), help_rect):
                    help_screen()
                    break

                # Check arrow buttons for each option
                base_y = 140
                spacing = 100
                for idx, (label, valfunc) in enumerate(opts):
                    y = base_y + idx * spacing
                    left = pygame.Rect(centerx - 160, y + 10, 40, 36)
                    right = pygame.Rect(centerx + 120, y + 10, 40, 36)
                    if point_in_rect((mx, my), left):
                        if idx == 0:  # Board size -
                            b_n = max(3, b_n - 1)
                            if win_l > b_n:
                                win_l = b_n
                        elif idx == 1:  # Player toggle
                            h_play = 'O' if h_play == 'X' else 'X'
                        elif idx == 2:  # max depth -
                            max_d = max(1, max_d - 1)
                        elif idx == 3:  # win length -
                            win_l = max(3, win_l - 1)
                        break
                    if point_in_rect((mx, my), right):
                        if idx == 0:
                            b_n = min(9, b_n + 1)
                        elif idx == 1:
                            h_play = 'O' if h_play == 'X' else 'X'
                        elif idx == 2:
                            max_d = min(12, max_d + 1)
                        elif idx == 3:
                            win_l = min(b_n, win_l + 1)
                        break

            elif ev.type == KEYDOWN:
                if ev.key == K_r:
                    # allow keyboard R to show help quickly (same as help button)
                    help_screen()

        # Render settings screen
        screen.fill(BG_COLOR)
        title = font.render("Game Settings", True, (220, 240, 255))
        screen.blit(title, (WINDOW_SIZE//2 - title.get_width()//2, 40))

        # Draw each option with arrow buttons
        base_y = 140
        spacing = 100
        for idx, (label, valfunc) in enumerate(opts):
            y = base_y + idx * spacing
            draw_label_value(screen, label, valfunc(), centerx, y)

            left = pygame.Rect(centerx - 160, y + 10, 40, 36)
            right = pygame.Rect(centerx + 120, y + 10, 40, 36)
            pygame.draw.rect(screen, (18, 24, 40), left, border_radius=6)
            pygame.draw.rect(screen, (18, 24, 40), right, border_radius=6)
            pygame.draw.rect(screen, NEON_GRID, left, 2, border_radius=6)
            pygame.draw.rect(screen, NEON_GRID, right, 2, border_radius=6)

            lt = small_font.render("<", True, (220, 240, 255))
            rt = small_font.render(">", True, (220, 240, 255))
            screen.blit(lt, lt.get_rect(center=left.center))
            screen.blit(rt, rt.get_rect(center=right.center))

            # helper hint below each
            hint = small_font.render({
                0: "Choose board dimension N (3..9).",
                1: "Choose your mark. If you pick O, AI starts.",
                2: "Cap AI search depth. Higher = stronger but slower.",
                3: "Number in a row required to win. 'Auto' = board size."
            }[idx], True, (170, 190, 210))
            screen.blit(hint, (centerx - hint.get_width()//2, y + 58))

        # Start and Help buttons
        draw_button(screen, start_rect, "Start Game")
        draw_button(screen, help_rect, "Help")

        pygame.display.flip()
        clock.tick(FPS)


# ============================
# Utility functions
# ============================

def in_bounds(r, c):
    return 0 <= r < BOARD_N and 0 <= c < BOARD_N


def lines_iter():
    """Yield all lines (as list of (r,c)) that could contain a WIN_LENGTH in a row.
    Includes rows, cols, and both diagonal directions."""
    # Rows
    for r in range(BOARD_N):
        yield [(r, c) for c in range(BOARD_N)]
    # Cols
    for c in range(BOARD_N):
        yield [(r, c) for r in range(BOARD_N)]
    # Diagonals (top-left to bottom-right)
    for start_r in range(BOARD_N):
        d = []
        r, c = start_r, 0
        while in_bounds(r, c):
            d.append((r, c))
            r += 1; c += 1
        if len(d) >= WIN_LENGTH:
            yield d
    for start_c in range(1, BOARD_N):
        d = []
        r, c = 0, start_c
        while in_bounds(r, c):
            d.append((r, c))
            r += 1; c += 1
        if len(d) >= WIN_LENGTH:
            yield d
    # Anti-diagonals (top-right to bottom-left)
    for start_r in range(BOARD_N):
        d = []
        r, c = start_r, BOARD_N - 1
        while in_bounds(r, c):
            d.append((r, c))
            r += 1; c -= 1
        if len(d) >= WIN_LENGTH:
            yield d
    for start_c in range(BOARD_N-2, -1, -1):
        d = []
        r, c = 0, start_c
        while in_bounds(r, c):
            d.append((r, c))
            r += 1; c -= 1
        if len(d) >= WIN_LENGTH:
            yield d


def check_winner(b):
    """Return 'X' or 'O' if someone has won, 'draw' if board full, else None."""
    # Check all lines by sliding window of length WIN_LENGTH
    for line in lines_iter():
        # slide
        for i in range(0, len(line) - WIN_LENGTH + 1):
            window = line[i:i+WIN_LENGTH]
            vals = [b[r][c] for (r,c) in window]
            if vals.count('X') == WIN_LENGTH:
                return 'X'
            if vals.count('O') == WIN_LENGTH:
                return 'O'
    # draw?
    if all(b[r][c] != EMPTY for r in range(BOARD_N) for c in range(BOARD_N)):
        return 'draw'
    return None


def evaluate(b):
    """Heuristic evaluation from AI_PLAYS perspective.
    Score > 0 favors AI, < 0 favors human. Terminal states return +/-inf or 0."""
    w = check_winner(b)
    if w == AI_PLAYS:
        return 1_000_000
    if w == HUMAN_PLAYS:
        return -1_000_000
    if w == 'draw':
        return 0
    # Non-terminal: count open sequences of various lengths
    score = 0
    for line in lines_iter():
        cells = [b[r][c] for (r,c) in line]
        # slide windows
        for i in range(0, len(cells) - WIN_LENGTH + 1):
            window = cells[i:i+WIN_LENGTH]
            if HUMAN_PLAYS in window and AI_PLAYS in window:
                continue  # blocked
            count_ai = window.count(AI_PLAYS)
            count_hu = window.count(HUMAN_PLAYS)
            if count_ai and not count_hu:
                # exponential weight for longer chains
                score += 10 ** count_ai
            elif count_hu and not count_ai:
                score -= 10 ** count_hu
    return score


def legal_moves(b):
    return [(r, c) for r in range(BOARD_N) for c in range(BOARD_N) if b[r][c] == EMPTY]


def make_move(b, r, c, p):
    b[r][c] = p


def undo_move(b, r, c):
    b[r][c] = EMPTY


def order_moves(moves, b, player):
    """Simple move ordering: prefer center, then corners, then others."""
    center = (BOARD_N - 1) / 2.0
    def priority(mc):
        r, c = mc
        dist = abs(r - center) + abs(c - center)
        corner_bonus = 0
        if (r in (0, BOARD_N-1)) and (c in (0, BOARD_N-1)):
            corner_bonus = -0.25
        return dist + corner_bonus
    return sorted(moves, key=priority)


def alphabeta(b, depth, alpha, beta, maximizing):
    winner = check_winner(b)
    if winner is not None:
        return evaluate(b), None
    if depth == 0:
        return evaluate(b), None

    best_move = None
    moves = legal_moves(b)
    moves = order_moves(moves, b, AI_PLAYS if maximizing else HUMAN_PLAYS)

    if maximizing:
        value = -math.inf
        for (r,c) in moves:
            make_move(b, r, c, AI_PLAYS)
            score, _ = alphabeta(b, depth-1, alpha, beta, False)
            undo_move(b, r, c)
            if score > value:
                value, best_move = score, (r, c)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = math.inf
        for (r,c) in moves:
            make_move(b, r, c, HUMAN_PLAYS)
            score, _ = alphabeta(b, depth-1, alpha, beta, True)
            undo_move(b, r, c)
            if score < value:
                value, best_move = score, (r, c)
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move


def ai_choose_move(b):
    empties = sum(1 for r in range(BOARD_N) for c in range(BOARD_N) if b[r][c] == EMPTY)
    # Dynamic depth: search deeper early when board is empty (lower branching),
    # and shallower late when nearly full (to keep UI responsive for large N).
    if BOARD_N <= 3:
        depth = 9  # full search for 3x3
    else:
        depth = min(MAX_DEPTH, max(3, min(6, empties // 2)))
    _, move = alphabeta(b, depth, -math.inf, math.inf, True)
    # Fallback if pruning returns None (shouldn't happen normally)
    if move is None:
        lm = legal_moves(b)
        move = lm[0] if lm else None
    return move


# ============================
# Rendering (neon glow)
# ============================

def draw_glow_line(surf, start, end, color, thickness=4):
    # Draw a glow by layering lines with increasing blur (via alpha + width)
    r, g, b = color
    for i in range(GLOW_STEPS, 0, -1):
        alpha = int(255 * (i / (GLOW_STEPS*2)))
        width = int(thickness + (i * 2))
        glow_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.line(glow_surf, (r, g, b, alpha), start, end, width)
        surf.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_ADD)
    pygame.draw.line(surf, color, start, end, thickness)


def draw_glow_circle(surf, center, radius, color, thickness=4):
    r, g, b = color
    for i in range(GLOW_STEPS, 0, -1):
        alpha = int(255 * (i / (GLOW_STEPS*2)))
        w = int(thickness + (i * 2))
        glow_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (r, g, b, alpha), center, radius, w)
        surf.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_ADD)
    pygame.draw.circle(surf, color, center, radius, thickness)


def draw_board():
    screen.fill(BG_COLOR)
    # Draw board grid
    for i in range(1, BOARD_N):
        x = GRID_ORIGIN[0] + i * CELL_SIZE
        y1 = GRID_ORIGIN[1]
        y2 = GRID_ORIGIN[1] + BOARD_N * CELL_SIZE
        draw_glow_line(screen, (x, y1), (x, y2), NEON_GRID, LINE_THICKNESS)
    for i in range(1, BOARD_N):
        y = GRID_ORIGIN[1] + i * CELL_SIZE
        x1 = GRID_ORIGIN[0]
        x2 = GRID_ORIGIN[0] + BOARD_N * CELL_SIZE
        draw_glow_line(screen, (x1, y), (x2, y), NEON_GRID, LINE_THICKNESS)

    # Marks
    pad = CELL_SIZE // 6
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            mark = board[r][c]
            x = GRID_ORIGIN[0] + c * CELL_SIZE
            y = GRID_ORIGIN[1] + r * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            if mark == 'X':
                p1 = (rect.left + pad, rect.top + pad)
                p2 = (rect.right - pad, rect.bottom - pad)
                p3 = (rect.right - pad, rect.top + pad)
                p4 = (rect.left + pad, rect.bottom - pad)
                draw_glow_line(screen, p1, p2, NEON_X, LINE_THICKNESS)
                draw_glow_line(screen, p3, p4, NEON_X, LINE_THICKNESS)
            elif mark == 'O':
                center = rect.center
                radius = (CELL_SIZE // 2) - pad
                draw_glow_circle(screen, center, radius, NEON_O, LINE_THICKNESS)

    # Side panel (menu/help)
    pygame.draw.rect(screen, (10, 12, 20), PANEL_RECT, border_radius=8)
    pygame.draw.rect(screen, NEON_GRID, PANEL_RECT, 2, border_radius=8)

    # Buttons inside panel
    btn_w = PANEL_RECT.width - 32
    btn_h = 48
    btn_x = PANEL_RECT.left + 16
    main_btn_rect = pygame.Rect(btn_x, PANEL_RECT.top + 24, btn_w, btn_h)
    help_btn_rect = pygame.Rect(btn_x, PANEL_RECT.top + 24 + btn_h + 12, btn_w, btn_h)
    draw_button(screen, main_btn_rect, "Main Menu")
    draw_button(screen, help_btn_rect, "Help")

    # Status text
    w = check_winner(board)
    if w is None:
        txt = f"Turn: {current_player}  |  {BOARD_N}x{BOARD_N}  win={WIN_LENGTH}"
    elif w == 'draw':
        txt = "Draw! Press R to restart"
    else:
        txt = f"{w} wins! Press R to restart"
    text_surf = small_font.render(txt, True, (180, 200, 230))
    screen.blit(text_surf, (MARGIN, WINDOW_SIZE - MARGIN))

    # Small legend inside panel
    legend_y = help_btn_rect.bottom + 20
    hint_lines = [
        f"Board: {BOARD_N}x{BOARD_N}",
        f"Win length: {WIN_LENGTH}",
        f"AI depth cap: {MAX_DEPTH}",
    ]
    for i, line in enumerate(hint_lines):
        txt = small_font.render(line, True, (200, 220, 240))
        screen.blit(txt, (PANEL_RECT.left + 16, legend_y + i*24))

    # Save rects for click handling
    draw_board.main_btn_rect = main_btn_rect
    draw_board.help_btn_rect = help_btn_rect

    pygame.display.flip()


# ============================
# Input helpers
# ============================

def pos_to_cell(mx, my):
    gx, gy = GRID_ORIGIN
    if not (gx <= mx < gx + BOARD_N*CELL_SIZE and gy <= my < gy + BOARD_N*CELL_SIZE):
        return None
    c = (mx - gx) // CELL_SIZE
    r = (my - gy) // CELL_SIZE
    return int(r), int(c)


def reset():
    global board, current_player, move_history
    # prepare dynamic structures for the current BOARD_N
    prepare_game()
    move_history = []
    # If human chose 'O', AI starts
    if HUMAN_PLAYS == 'O':
        current_player = 'X'
        ai_move()
    else:
        current_player = 'X'


# ============================
# AI driver
# ============================

def ai_move():
    global current_player
    if check_winner(board) is not None:
        return
    move = ai_choose_move(board)
    if move:
        r, c = move
        if board[r][c] == EMPTY:
            make_move(board, r, c, AI_PLAYS)
            move_history.append((r, c))
            current_player = HUMAN_PLAYS


# ============================
# Main loop
# ============================

# Show settings UI before starting the game loop
settings_screen()
# ensure game state reflects chosen settings
prepare_game()
reset()

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_r:
                # Restart current game (keeps settings)
                reset()
            elif event.key == K_u:
                # Undo last human move if it's AI's turn (optional)
                if current_player == AI_PLAYS and move_history:
                    # If last was AI move, undo it and also the preceding human move
                    last_r, last_c = move_history.pop()
                    undo_move(board, last_r, last_c)
                    # Try to find the preceding human move in history by scanning backwards
                    for idx in range(len(move_history)-1, -1, -1):
                        r, c = move_history[idx]
                        if board[r][c] == HUMAN_PLAYS:
                            undo_move(board, r, c)
                            move_history.pop(idx)
                            break
                    current_player = HUMAN_PLAYS
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Handle clicks on side panel buttons first
            if hasattr(draw_board, 'main_btn_rect') and hasattr(draw_board, 'help_btn_rect'):
                if point_in_rect((mx, my), draw_board.main_btn_rect):
                    # Open main/settings screen
                    settings_screen()
                    # reapply changes
                    prepare_game()
                    reset()
                    continue
                if point_in_rect((mx, my), draw_board.help_btn_rect):
                    help_screen()
                    continue

            # Otherwise handle board clicks
            if check_winner(board) is None and current_player == HUMAN_PLAYS:
                cell = pos_to_cell(*event.pos)
                if cell:
                    r, c = cell
                    if board[r][c] == EMPTY:
                        make_move(board, r, c, HUMAN_PLAYS)
                        move_history.append((r, c))
                        current_player = AI_PLAYS
                        draw_board()
                        if check_winner(board) is None:
                            ai_move()

    draw_board()
    clock.tick(FPS)

pygame.quit()
sys.exit()
