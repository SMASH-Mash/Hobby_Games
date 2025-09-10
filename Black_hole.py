import pygame
import sys
import math
import random

pygame.init()
WIDTH, HEIGHT = 800, 600
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

# Game state
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
        self.draw_number_panel(1, 50)
        self.draw_number_panel(2, HEIGHT-100)
        # Current player indicator
        info = FONT.render(f"Player {self.current_player}'s turn", True, RED if self.current_player==1 else GREEN)
        SCREEN.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 - 20))

    def draw_number_panel(self, player, y_offset):
        x_start = 50
        for idx, num in enumerate(range(1,11)):
            x = x_start + idx*50
            color = GRAY if num not in self.available_numbers[player] else RED if player==1 else GREEN
            rect = pygame.Rect(x, y_offset, 40,40)
            pygame.draw.rect(SCREEN, color, rect)
            num_txt = FONT.render(str(num), True, BLACK)
            SCREEN.blit(num_txt, (x+20 - num_txt.get_width()//2, y_offset+20 - num_txt.get_height()//2))
            self.num_panels[player].append((num, rect))

    def handle_click(self, pos):
        if self.state=="menu":
            for name,btn in self.main_menu_buttons:
                if btn.collidepoint(pos):
                    if name=="pvp":
                        self.vs_ai=False
                    else:
                        self.vs_ai=True
                        self.ai_depth=2
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
                    # Check end
                    if all(v is not None for v in self.board[:-1]):
                        self.determine_winner()
                        return
                    self.current_player = 2 if self.current_player==1 else 1
                    if self.vs_ai and self.current_player==2:
                        pygame.time.set_timer(pygame.USEREVENT, 500)

    def ai_move(self):
        choices = list(self.available_numbers[2])
        if not choices:
            return
        num = random.choice(choices)
        empties = [i for i,v in enumerate(self.board) if v is None]
        idx = random.choice(empties)
        self.board[idx]=(2,num)
        self.available_numbers[2].remove(num)
        self.last_placed=idx
        # Check end
        if all(v is not None for v in self.board[:-1]):
            self.determine_winner()
            return
        self.current_player=1

    def determine_winner(self):
        # Black hole is last empty
        black = self.board.index(None)
        adj = self.get_adjacent(black)
        scores = {1:0,2:0}
        for i in adj:
            if self.board[i]:
                player,num = self.board[i]
                scores[player]+=num
        self.winner = 1 if scores[1]<scores[2] else 2
        self.state="gameover"

    def draw_gameover(self):
        SCREEN.fill(BLACK)
        msg = BIGFONT.render(f"Player {self.winner} Wins!", True, RED if self.winner==1 else GREEN)
        SCREEN.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - msg.get_height()//2))
        back_btn = pygame.Rect(WIDTH//2 -100, HEIGHT//2 +100, 200,50)
        pygame.draw.rect(SCREEN, RED, back_btn)
        txt = FONT.render("Back to Menu", True, BLACK)
        SCREEN.blit(txt, (back_btn.centerx - txt.get_width()//2, back_btn.centery - txt.get_height()//2))
        self.back_btn = back_btn

    def reset_game(self):
        self.board = [None]*21
        self.current_player=1
        self.last_placed=None
        self.available_numbers={1:set(range(1,11)), 2:set(range(1,11))}
        self.selected_number=None
        self.winner=None
        self.num_panels={1:[],2:[]}

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
                pygame.time.set_timer(pygame.USEREVENT, 0)
    if game.state=="menu":
        game.draw_menu()
    elif game.state=="playing":
        game.draw_board()
    elif game.state=="gameover":
        game.draw_gameover()
    pygame.display.flip()
pygame.quit()
sys.exit()
