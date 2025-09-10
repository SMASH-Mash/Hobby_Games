import pygame, sys, math

pygame.init()
WIDTH, HEIGHT = 900, 650
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Black Hole Pyramid")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("Consolas", 20)
BIGFONT = pygame.font.SysFont("Consolas", 40)

# Colors
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
GRAY = (100,100,100)
WHITE = (255,255,255)

class Game:
    def __init__(self):
        self.state = "menu" # menu, playing, gameover
        self.vs_ai = False
        self.ai_depth = 2
        self.current_player = 1
        self.board = [None]*21
        self.last_placed = None
        self.available_numbers = {1:set(range(1,11)), 2:set(range(1,11))}
        self.selected_number = None
        self.winner = None
        self.main_menu_buttons = []
        self.num_panels = {1:[], 2:[]}
        self.circle_positions = self.get_circle_positions()

    def get_circle_positions(self):
        positions = {}
        idx = 0
        for row in range(6):
            y = 80 + row*70
            start_x = WIDTH//2 - row*50
            for col in range(row+1):
                x = start_x + col*100
                positions[idx] = (x,y)
                idx+=1
        return positions

    # --- Drawing Functions ---
    def draw_menu(self):
        SCREEN.fill(BLACK)
        title = BIGFONT.render("Black Hole Pyramid", True, RED)
        SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        # Buttons
        self.main_menu_buttons = []
        pvp_btn = pygame.Rect(WIDTH//2 - 100, 200, 200, 50)
        pygame.draw.rect(SCREEN, RED, pvp_btn)
        txt = FONT.render("Play vs Player", True, BLACK)
        SCREEN.blit(txt, (pvp_btn.centerx - txt.get_width()//2, pvp_btn.centery - txt.get_height()//2))
        self.main_menu_buttons.append(("pvp", pvp_btn))

        pvai_btn = pygame.Rect(WIDTH//2 - 100, 300, 200, 50)
        pygame.draw.rect(SCREEN, RED, pvai_btn)
        txt2 = FONT.render("Play vs AI", True, BLACK)
        SCREEN.blit(txt2, (pvai_btn.centerx - txt2.get_width()//2, pvai_btn.centery - txt2.get_height()//2))
        self.main_menu_buttons.append(("pvai", pvai_btn))

        depth_txt = FONT.render(f"AI Depth: {self.ai_depth}", True, RED)
        SCREEN.blit(depth_txt, (WIDTH//2 - depth_txt.get_width()//2, 400))

    def draw_board(self):
        SCREEN.fill(BLACK)
        # Draw circles
        for idx,(x,y) in self.circle_positions.items():
            color = GRAY if self.board[idx] is None else RED if self.board[idx][0]==1 else GREEN
            pygame.draw.circle(SCREEN, color, (x,y), 25)
            if self.board[idx] is not None:
                num_txt = FONT.render(str(self.board[idx][1]), True, WHITE)
                SCREEN.blit(num_txt, (x - num_txt.get_width()//2, y - num_txt.get_height()//2))
        # Highlight last placed
        if self.last_placed is not None:
            x,y = self.circle_positions[self.last_placed]
            pygame.draw.circle(SCREEN, WHITE, (x,y), 28,3)
        # Draw number panels
        self.draw_number_panel(1, 500)
        self.draw_number_panel(2, 50)
        # Current player indicator
        info = FONT.render(f"Player {self.current_player}'s turn", True, RED if self.current_player==1 else GREEN)
        SCREEN.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 - 20))

    def draw_number_panel(self, player, y_offset):
        x_start = 50
        self.num_panels[player]=[]
        for idx, num in enumerate(range(1,11)):
            x = x_start + idx*70
            color = GRAY if num not in self.available_numbers[player] else RED if player==1 else GREEN
            rect = pygame.Rect(x, y_offset, 50,50)
            pygame.draw.rect(SCREEN, color, rect)
            num_txt = FONT.render(str(num), True, BLACK)
            SCREEN.blit(num_txt, (x+25 - num_txt.get_width()//2, y_offset+25 - num_txt.get_height()//2))
            self.num_panels[player].append((num, rect))

    def draw_gameover(self):
        SCREEN.fill(BLACK)
        msg = BIGFONT.render(f"Player {self.winner} Wins!", True, RED if self.winner==1 else GREEN)
        SCREEN.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 50))
        back_btn = pygame.Rect(WIDTH//2 -100, HEIGHT//2 +50, 200,50)
        pygame.draw.rect(SCREEN, RED, back_btn)
        txt = FONT.render("Back to Menu", True, BLACK)
        SCREEN.blit(txt, (back_btn.centerx - txt.get_width()//2, back_btn.centery - txt.get_height()//2))
        self.back_btn = back_btn

    # --- Event Handling ---
    def handle_click(self, pos):
        if self.state=="menu":
            for name,btn in self.main_menu_buttons:
                if btn.collidepoint(pos):
                    if name=="pvp":
                        self.vs_ai=False
                    else:
                        self.vs_ai=True
                    self.state="playing"
                    self.reset_game()
        elif self.state=="playing":
            # Check number panel clicks
            for num,rect in self.num_panels[self.current_player]:
                if rect.collidepoint(pos) and num in self.available_numbers[self.current_player]:
                    self.selected_number=num
            # Check board clicks
            for idx,(x,y) in self.circle_positions.items():
                circle_rect = pygame.Rect(x-25,y-25,50,50)
                if circle_rect.collidepoint(pos) and self.board[idx] is None and self.selected_number:
                    self.board[idx]=(self.current_player, self.selected_number)
                    self.available_numbers[self.current_player].remove(self.selected_number)
                    self.last_placed = idx
                    self.selected_number=None
                    if all(v is not None for v in self.board[:-1]):
                        self.determine_winner()
                        return
                    self.current_player = 2 if self.current_player==1 else 1
                    if self.vs_ai and self.current_player==2:
                        pygame.time.set_timer(pygame.USEREVENT, 500)
        elif self.state=="gameover":
            if self.back_btn.collidepoint(pos):
                self.state="menu"

    # --- AI Functions ---
    def ai_move(self):
        best_score = -math.inf
        best_move = None
        empties = [i for i,v in enumerate(self.board) if v is None]
        for num in self.available_numbers[2]:
            for idx in empties:
                new_board = self.board.copy()
                new_board[idx] = (2,num)
                score = self.minimax(new_board, self.available_numbers[2]-{num}, self.available_numbers[1], self.ai_depth-1, False, -math.inf, math.inf)
                if score > best_score:
                    best_score = score
                    best_move = (idx, num)
        if best_move:
            idx, num = best_move
            self.board[idx] = (2,num)
            self.available_numbers[2].remove(num)
            self.last_placed = idx
            if all(v is not None for v in self.board[:-1]):
                self.determine_winner()
                return
            self.current_player = 1

    def minimax(self, board, ai_nums, opp_nums, depth, maximizing, alpha, beta):
        if depth==0 or all(v is not None for v in board[:-1]):
            return self.evaluate_board(board)
        empties = [i for i,v in enumerate(board) if v is None]
        if maximizing:
            max_eval = -math.inf
            for num in ai_nums:
                for idx in empties:
                    new_board = board.copy()
                    new_board[idx]=(2,num)
                    eval = self.minimax(new_board, ai_nums-{num}, opp_nums, depth-1, False, alpha, beta)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = math.inf
            for num in opp_nums:
                for idx in empties:
                    new_board = board.copy()
                    new_board[idx]=(1,num)
                    eval = self.minimax(new_board, ai_nums, opp_nums-{num}, depth-1, True, alpha, beta)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
            return min_eval

    def evaluate_board(self, board):
        black = next((i for i,v in enumerate(board) if v is None), None)
        if black is None:
            return 0
        adj = self.get_adjacent(black)
        scores = {1:0, 2:0}
        for i in adj:
            if board[i]:
                player,num = board[i]
                scores[player]+=num
        return scores[1] - scores[2]

    # --- Game Logic ---
    def determine_winner(self):
        black = self.board.index(None)
        adj = self.get_adjacent(black)
        scores = {1:0,2:0}
        for i in adj:
            if self.board[i]:
                player,num = self.board[i]
                scores[player]+=num
        self.winner = 1 if scores[1]<scores[2] else 2
        self.state="gameover"

    def get_adjacent(self, idx):
        layer = int((math.sqrt(8*idx+1)-1)//2)
        pos = idx - layer*(layer+1)//2
        neighbors=[]
        if layer>0:
            above_start=(layer-1)*layer//2
            neighbors.append(above_start+pos)
            if pos>0:
                neighbors.append(above_start+pos-1)
        if layer<5:
            below_start=(layer+1)*(layer+2)//2 - (layer+1)
            neighbors.append(below_start+pos)
            neighbors.append(below_start+pos+1)
        return [n for n in neighbors if 0<=n<21]

    def reset_game(self):
        self.board = [None]*21
        self.current_player=1
        self.last_placed=None
        self.available_numbers={1:set(range(1,11)), 2:set(range(1,11))}
        self.selected_number=None
        self.winner=None
        self.num_panels={1:[],2:[]}

# --- Main Loop ---
game = Game()
running = True
while running:
    CLOCK.tick(30)
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        elif event.type==pygame.MOUSEBUTTONDOWN:
            game.handle_click(event.pos)
        elif event.type==pygame.USEREVENT:
            if game.vs_ai and game.current_player==2 and game.state=="playing":
                game.ai_move()
                pygame.time.set_timer(pygame.USEREVENT,0)

    if game.state=="menu":
        game.draw_menu()
    elif game.state=="playing":
        game.draw_board()
    elif game.state=="gameover":
        game.draw_gameover()

    pygame.display.flip()

pygame.quit()
sys.exit()
