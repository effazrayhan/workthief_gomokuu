import turtle
import time
import random
from enum import Enum

# Global score variables
user_win = 0
ai_win = 0
round_number = 1

def reset_scores():
    global user_win, ai_win, round_number
    user_win = 0
    ai_win = 0
    round_number = 1

# Constants
BOARD_SIZE = 10
MAX_WIDTH = 1080
MAX_HEIGHT = 720
WIN_LENGTH = 5
MAX_DEPTH = 5

# Colors (RGB normalized)
WHITE_COLOR = (1, 1, 1)
BLACK_COLOR = (0.1, 0.1, 0.1)
BOARD_COLOR = (254/255, 194/255, 35/255)
GOLD_COLOR = (255/255, 215/255, 0)
GREEN_COLOR = (50/255, 255/255, 50/255)
RED_COLOR = (255/255, 50/255, 50/255)
ORANGE_COLOR = (255/255, 200/255, 50/255)
GRAY_COLOR = (100/255, 100/255, 140/255)

# Window dimensions
WIN_W = 1080
WIN_H = 720

# Game states
class GameState(Enum):
    MENU = 1
    COIN_SELECT = 2
    PLAYING = 3
    PAUSED = 4
    GAME_OVER = 5

# Cell values
class Cell:
    EMPTY = 0
    BLACK = 1
    WHITE = 2

# Transposition table for AI
class TranspositionTable:
    def __init__(self):
        self.cache = {}
    
    def board_to_key(self, board):
        return tuple(board)
    
    def contains(self, board):
        return self.board_to_key(board) in self.cache
    
    def get(self, board):
        return self.cache.get(self.board_to_key(board), 0)
    
    def set(self, board, value):
        self.cache[self.board_to_key(board)] = value
    
    def clear(self):
        self.cache.clear()

# Button class
class Button:
    def __init__(self, x, y, width, height, text):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
    
    def contains(self, px, py):
        return (self.x <= px <= self.x + self.width and 
                self.y <= py <= self.y + self.height)
    
    def draw(self, pen):
        pen.penup()
        pen.goto(self.x, self.y)
        pen.pendown()
        pen.color("black")
        pen.fillcolor(GRAY_COLOR)
        pen.pensize(2)
        pen.begin_fill()
        for _ in range(2):
            pen.forward(self.width)
            pen.left(90)
            pen.forward(self.height)
            pen.left(90)
        pen.end_fill()
        
        # Draw text
        pen.penup()
        pen.goto(self.x + self.width/2, self.y + self.height/2 - 8)
        pen.color("white")
        pen.write(self.text, align="center", font=("Google Sans Flex", 14, "bold"))

# Game class
class GomokuGame:
    def __init__(self):
        self.state = GameState.MENU
        self.board = [Cell.EMPTY] * (BOARD_SIZE * BOARD_SIZE)
        self.human_color = Cell.WHITE
        self.computer_color = Cell.BLACK
        self.player_turn = True
        self.winner = Cell.EMPTY
        self.game_ended = False
        self.score_updated = False
        self.tt = TranspositionTable()
        
        # Setup turtle
        self.screen = turtle.Screen()
        self.screen.setup(WIN_W, WIN_H)
        self.screen.title("Gomoku - WorkThief")
        self.screen.bgcolor(BLACK_COLOR)
        self.screen.tracer(0)
        
        # Create pens
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0)
        
        # Board layout - positioned on right side
        board_margin = 40
        board_size_px = min(WIN_W - 2 * board_margin - 200, WIN_H - 2 * board_margin - 60)
        self.cell_size = board_size_px / (BOARD_SIZE - 1)
        self.board_origin_x = WIN_W/2 - board_size_px - board_margin - 100
        self.board_origin_y = -board_size_px/2 + 20
        
        # Buttons
        self.create_buttons()
        
        # Bind mouse events
        self.screen.onclick(self.handle_click)
        self.screen.onkey(self.handle_escape, "Escape")
        self.screen.listen()
        
        self.draw()
    
    def create_buttons(self):
        # Menu buttons
        self.start_btn = Button(-120, -210, 240, 50, "Start Game")
        self.exit_btn = Button(-120, -270, 240, 50, "Exit")
        
        # Coin select buttons
        self.white_btn = Button(-150, -210, 300, 50, "White (W)")
        self.black_btn = Button(-150, -270, 300, 50, "Black (B)")
        self.back_btn = Button(-WIN_W/2 + 20, WIN_H/2 - 60, 100, 36, "Back")
        
        # Game over buttons
        self.new_game_btn = Button(-WIN_W/2 + 50, 230, 250, 50, "New Game")
        self.main_menu_btn = Button(-WIN_W/2 + 50, 170, 250, 50, "Main Menu")
    
    def index(self, r, c):
        return r * BOARD_SIZE + c
    
    def reset_board(self):
        self.board = [Cell.EMPTY] * (BOARD_SIZE * BOARD_SIZE)
        self.winner = Cell.EMPTY
        self.game_ended = False
        self.score_updated = False
        self.tt.clear()
    
    def board_pos_to_cell(self, x, y):
        rel_x = x - self.board_origin_x
        rel_y = y - self.board_origin_y
        
        if rel_x < -self.cell_size * 0.5 or rel_y < -self.cell_size * 0.5:
            return -1, -1
        
        c = int((rel_x + self.cell_size * 0.5) / self.cell_size + 0.0001)
        r = int((rel_y + self.cell_size * 0.5) / self.cell_size + 0.0001)
        
        if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
            return -1, -1
        
        return r, c
    
    def check_win(self, board_state, player):
        # Check all directions for 5 in a row
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board_state[self.index(r, c)] != player:
                    continue
                
                # Horizontal
                if c <= BOARD_SIZE - WIN_LENGTH:
                    win = True
                    for i in range(1, WIN_LENGTH):
                        if board_state[self.index(r, c + i)] != player:
                            win = False
                            break
                    if win:
                        return True
                
                # Vertical
                if r <= BOARD_SIZE - WIN_LENGTH:
                    win = True
                    for i in range(1, WIN_LENGTH):
                        if board_state[self.index(r + i, c)] != player:
                            win = False
                            break
                    if win:
                        return True
                
                # Diagonal
                if r <= BOARD_SIZE - WIN_LENGTH and c <= BOARD_SIZE - WIN_LENGTH:
                    win = True
                    for i in range(1, WIN_LENGTH):
                        if board_state[self.index(r + i, c + i)] != player:
                            win = False
                            break
                    if win:
                        return True
                
                # Anti-diagonal
                if r <= BOARD_SIZE - WIN_LENGTH and c >= WIN_LENGTH - 1:
                    win = True
                    for i in range(1, WIN_LENGTH):
                        if board_state[self.index(r + i, c - i)] != player:
                            win = False
                            break
                    if win:
                        return True
        
        return False
    
    def check_board_full(self):
        return all(cell != Cell.EMPTY for cell in self.board)
    
    def generate_candidate_moves(self, board_state):
        moves = []
        
        # If board is empty, start near center
        has_pieces = any(cell != Cell.EMPTY for cell in board_state)
        
        if not has_pieces:
            center = BOARD_SIZE // 2
            random_row = center + random.randint(-2, 2)
            random_col = center + random.randint(-2, 2)
            random_row = max(2, min(BOARD_SIZE - 3, random_row))
            random_col = max(2, min(BOARD_SIZE - 3, random_col))
            moves.append((random_row, random_col))
            return moves
        
        # Find moves near existing pieces
        considered = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board_state[self.index(r, c)] != Cell.EMPTY:
                    for dr in range(-2, 3):
                        for dc in range(-2, 3):
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and
                                not considered[nr][nc] and 
                                board_state[self.index(nr, nc)] == Cell.EMPTY):
                                considered[nr][nc] = True
                                moves.append((nr, nc))
        
        # Add center if not included
        center = BOARD_SIZE // 2
        if board_state[self.index(center, center)] == Cell.EMPTY:
            moves.insert(0, (center, center))
        
        return moves
    
    def evaluate_board(self, board_state, ai_player):
        opponent = Cell.BLACK if ai_player == Cell.BLACK else Cell.WHITE
        score = 0
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board_state[self.index(r, c)] != Cell.EMPTY:
                    continue
                
                directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
                
                for dr, dc in directions:
                    ai_count = 0
                    opponent_count = 0
                    
                    # Forward
                    for i in range(1, 5):
                        nr, nc = r + i * dr, c + i * dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            cell = board_state[self.index(nr, nc)]
                            if cell == ai_player:
                                ai_count += 1
                            elif cell == opponent:
                                opponent_count += 1
                                break
                            else:
                                break
                        else:
                            break
                    
                    # Backward
                    for i in range(1, 5):
                        nr, nc = r - i * dr, c - i * dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            cell = board_state[self.index(nr, nc)]
                            if cell == ai_player:
                                ai_count += 1
                            elif cell == opponent:
                                opponent_count += 1
                                break
                            else:
                                break
                        else:
                            break
                    
                    # Score patterns
                    if opponent_count == 0:
                        if ai_count >= 4:
                            score += 10000
                        elif ai_count == 3:
                            score += 1000
                        elif ai_count == 2:
                            score += 100
                        elif ai_count == 1:
                            score += 10
                    
                    if ai_count == 0:
                        if opponent_count >= 4:
                            score -= 10000
                        elif opponent_count == 3:
                            score -= 1000
                        elif opponent_count == 2:
                            score -= 100
                        elif opponent_count == 1:
                            score -= 10
        
        return score
    
    def minimax(self, board_state, depth, alpha, beta, is_maximizing, ai_player):
        # Check cache
        if depth < MAX_DEPTH - 2:
            if self.tt.contains(board_state):
                return self.tt.get(board_state)
        
        opponent = Cell.WHITE if ai_player == Cell.BLACK else Cell.BLACK
        
        # Terminal conditions
        if self.check_win(board_state, ai_player):
            return 1000000 - depth
        if self.check_win(board_state, opponent):
            return -1000000 + depth
        if depth == 0 or all(cell != Cell.EMPTY for cell in board_state):
            eval_score = self.evaluate_board(board_state, ai_player)
            if depth < MAX_DEPTH - 2:
                self.tt.set(board_state, eval_score)
            return eval_score
        
        possible_moves = self.generate_candidate_moves(board_state)
        self.sort_moves_by_priority(possible_moves, board_state, ai_player)
        
        if len(possible_moves) > 15:
            possible_moves = possible_moves[:15]
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in possible_moves:
                board_state[self.index(move[0], move[1])] = ai_player
                eval_score = self.minimax(board_state, depth - 1, alpha, beta, False, ai_player)
                board_state[self.index(move[0], move[1])] = Cell.EMPTY
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            if depth < MAX_DEPTH - 2:
                self.tt.set(board_state, max_eval)
            return max_eval
        else:
            min_eval = float('inf')
            for move in possible_moves:
                board_state[self.index(move[0], move[1])] = opponent
                eval_score = self.minimax(board_state, depth - 1, alpha, beta, True, ai_player)
                board_state[self.index(move[0], move[1])] = Cell.EMPTY
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            if depth < MAX_DEPTH - 2:
                self.tt.set(board_state, min_eval)
            return min_eval
    
    def sort_moves_by_priority(self, moves, board_state, ai_player):
        opponent = Cell.WHITE if ai_player == Cell.BLACK else Cell.BLACK
        
        def get_priority(move):
            priority = 0
            
            # Check for immediate win
            temp_board = board_state[:]
            temp_board[self.index(move[0], move[1])] = ai_player
            if self.check_win(temp_board, ai_player):
                priority += 1000
            
            # Check for blocking opponent win
            temp_board = board_state[:]
            temp_board[self.index(move[0], move[1])] = opponent
            if self.check_win(temp_board, opponent):
                priority += 500
            
            # Center distance priority
            center_dist = abs(move[0] - BOARD_SIZE//2) + abs(move[1] - BOARD_SIZE//2)
            priority += (BOARD_SIZE - center_dist)
            
            return priority
        
        moves.sort(key=get_priority, reverse=True)
    
    def get_best_move(self, board_state, ai_player):
        best_move = (-1, -1)
        best_score = float('-inf')
        
        # Check for immediate win
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board_state[self.index(r, c)] == Cell.EMPTY:
                    board_state[self.index(r, c)] = ai_player
                    if self.check_win(board_state, ai_player):
                        best_move = (r, c)
                        board_state[self.index(r, c)] = Cell.EMPTY
                        return best_move
                    board_state[self.index(r, c)] = Cell.EMPTY
        
        # Check for blocking move
        opponent = Cell.WHITE if ai_player == Cell.BLACK else Cell.BLACK
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board_state[self.index(r, c)] == Cell.EMPTY:
                    board_state[self.index(r, c)] = opponent
                    if self.check_win(board_state, opponent):
                        best_move = (r, c)
                        board_state[self.index(r, c)] = Cell.EMPTY
                        return best_move
                    board_state[self.index(r, c)] = Cell.EMPTY
        
        # Use minimax
        possible_moves = self.generate_candidate_moves(board_state)
        self.sort_moves_by_priority(possible_moves, board_state, ai_player)
        
        if len(possible_moves) > 8:
            possible_moves = possible_moves[:8]
        
        alpha = float('-inf')
        beta = float('inf')
        
        for move in possible_moves:
            board_state[self.index(move[0], move[1])] = ai_player
            score = self.minimax(board_state, MAX_DEPTH - 1, alpha, beta, False, ai_player)
            board_state[self.index(move[0], move[1])] = Cell.EMPTY
            
            if score >= best_score:
                best_score = score
                best_move = move
        
        print(f"AI selected move: {best_move} with score {best_score}")
        return best_move
    
    def computer_move(self):
        if self.game_ended:
            return
        
        best_move = self.get_best_move(self.board, self.computer_color)
        if best_move[0] != -1:
            self.board[self.index(best_move[0], best_move[1])] = self.computer_color
            
            if self.check_win(self.board, self.computer_color):
                self.winner = self.computer_color
                self.game_ended = True
                self.state = GameState.GAME_OVER
            elif self.check_board_full():
                self.winner = Cell.EMPTY
                self.game_ended = True
                self.state = GameState.GAME_OVER
        
        self.player_turn = True
        self.draw()
    
    def handle_escape(self):
        if self.state == GameState.MENU:
            self.screen.bye()
        elif self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
            self.draw()
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
            self.draw()
        elif self.state == GameState.GAME_OVER:
            reset_scores()
            self.reset_board()
            self.score_updated = False
            self.state = GameState.MENU
            self.draw()
    
    def handle_click(self, x, y):
        global user_win, ai_win, round_number
        
        if self.state == GameState.MENU:
            if self.start_btn.contains(x, y):
                self.state = GameState.COIN_SELECT
                self.draw()
            elif self.exit_btn.contains(x, y):
                self.screen.bye()
        
        elif self.state == GameState.COIN_SELECT:
            if self.white_btn.contains(x, y):
                self.human_color = Cell.WHITE
                self.computer_color = Cell.BLACK
                self.reset_board()
                self.player_turn = True
                self.state = GameState.PLAYING
                self.draw()
            elif self.black_btn.contains(x, y):
                self.human_color = Cell.BLACK
                self.computer_color = Cell.WHITE
                self.reset_board()
                self.player_turn = False
                self.state = GameState.PLAYING
                self.draw()
                self.screen.ontimer(self.computer_move, 100)
            elif self.back_btn.contains(x, y):
                self.state = GameState.MENU
                self.draw()
        
        elif self.state == GameState.PLAYING:
            if not self.player_turn or self.game_ended:
                return
            
            r, c = self.board_pos_to_cell(x, y)
            
            if r != -1 and c != -1:
                idx = self.index(r, c)
                if self.board[idx] == Cell.EMPTY:
                    self.board[idx] = self.human_color
                    
                    if self.check_win(self.board, self.human_color):
                        self.winner = self.human_color
                        self.game_ended = True
                        self.state = GameState.GAME_OVER
                        self.draw()
                    elif self.check_board_full():
                        self.winner = Cell.EMPTY
                        self.game_ended = True
                        self.state = GameState.GAME_OVER
                        self.draw()
                    else:
                        self.player_turn = False
                        self.draw()
                        self.screen.ontimer(self.computer_move, 100)
        
        elif self.state == GameState.GAME_OVER:
            if self.new_game_btn.contains(x, y):
                self.reset_board()
                # Swap colors for fairness
                self.human_color, self.computer_color = self.computer_color, self.human_color
                
                if self.human_color == Cell.BLACK:
                    self.player_turn = False
                    self.state = GameState.PLAYING
                    self.draw()
                    self.screen.ontimer(self.computer_move, 100)
                else:
                    self.player_turn = True
                    self.state = GameState.PLAYING
                    self.draw()
            elif self.main_menu_btn.contains(x, y):
                self.state = GameState.MENU
                reset_scores()
                self.draw()
    
    def draw(self):
        global user_win, ai_win, round_number
        
        self.pen.clear()
        
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.COIN_SELECT:
            self.draw_coin_select()
        elif self.state == GameState.PLAYING or self.state == GameState.PAUSED:
            self.draw_board()
            if self.state == GameState.PAUSED:
                self.draw_paused_overlay()
        elif self.state == GameState.GAME_OVER:
            if not self.score_updated:
                round_number += 1
                if self.winner == self.human_color:
                    user_win += 1
                elif self.winner == self.computer_color:
                    ai_win += 1
                self.score_updated = True
                print(f"Game Over - Round: {round_number - 1}, User Wins: {user_win}, AI Wins: {ai_win}")
            self.draw_game_over()
        
        self.screen.update()
    
    def draw_menu(self):
        # Title
        self.pen.penup()
        self.pen.goto(0, 200)
        self.pen.color("white")
        self.pen.write("Gomoku", align="center", font=("Google Sans Flex", 48, "bold"))
        
        # Try to load intro image (optional)
        try:
            self.screen.bgpic("images/intro.png")
        except:
            pass
        
        # Draw buttons
        self.start_btn.draw(self.pen)
        self.exit_btn.draw(self.pen)
    
    def draw_coin_select(self):
        # Title
        self.pen.penup()
        self.pen.goto(0, 200)
        self.pen.color("white")
        self.pen.write("Choose Your Coin", align="center", font=("Google Sans Flex", 36, "bold"))
        
        # Draw buttons
        self.white_btn.draw(self.pen)
        self.black_btn.draw(self.pen)
        self.back_btn.draw(self.pen)
    
    def draw_board(self):
        # Draw board background
        self.pen.penup()
        self.pen.goto(self.board_origin_x - self.cell_size/2, self.board_origin_y - self.cell_size/2)
        self.pen.pendown()
        self.pen.color("black")
        self.pen.fillcolor(BOARD_COLOR)
        self.pen.pensize(2)
        self.pen.begin_fill()
        board_width = self.cell_size * BOARD_SIZE
        for _ in range(2):
            self.pen.forward(board_width)
            self.pen.left(90)
            self.pen.forward(board_width)
            self.pen.left(90)
        self.pen.end_fill()
        
        # Draw grid lines
        self.pen.pensize(1)
        self.pen.color("black")
        for i in range(BOARD_SIZE):
            # Horizontal lines
            self.pen.penup()
            self.pen.goto(self.board_origin_x, self.board_origin_y + i * self.cell_size)
            self.pen.pendown()
            self.pen.goto(self.board_origin_x + (BOARD_SIZE - 1) * self.cell_size, 
                         self.board_origin_y + i * self.cell_size)
            
            # Vertical lines
            self.pen.penup()
            self.pen.goto(self.board_origin_x + i * self.cell_size, self.board_origin_y)
            self.pen.pendown()
            self.pen.goto(self.board_origin_x + i * self.cell_size, 
                         self.board_origin_y + (BOARD_SIZE - 1) * self.cell_size)
        
        # Draw pieces
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                v = self.board[self.index(r, c)]
                if v == Cell.EMPTY:
                    continue
                
                center_x = self.board_origin_x + c * self.cell_size
                center_y = self.board_origin_y + r * self.cell_size
                
                self.pen.penup()
                self.pen.goto(center_x, center_y - self.cell_size * 0.4)
                self.pen.pendown()
                
                if v == Cell.BLACK:
                    self.pen.fillcolor(GRAY_COLOR)
                    self.pen.color("black")
                else:
                    self.pen.fillcolor(GRAY_COLOR)
                    self.pen.color("white")
                
                self.pen.pensize(2)
                self.pen.begin_fill()
                self.pen.circle(self.cell_size * 0.4)
                self.pen.end_fill()
        
        # Display scores on left side
        left_x = -WIN_W/2 + 50
        start_y = self.board_origin_y + self.cell_size * (BOARD_SIZE - 1) / 2
        
        # First turn info
        self.pen.penup()
        self.pen.goto(left_x, start_y + 40)
        self.pen.color(GOLD_COLOR)
        first_turn = "Human" if self.human_color == Cell.WHITE else "AI - CPU"
        self.pen.write(f"First Turn: {first_turn}", align="left", font=("Google Sans Flex", 12, "normal"))
        
        # Round number
        self.pen.penup()
        self.pen.goto(left_x, start_y)
        self.pen.color(GOLD_COLOR)
        self.pen.write(f"Round: {round_number}", align="left", font=("Google Sans Flex", 12, "normal"))
        
        # User wins
        self.pen.penup()
        self.pen.goto(left_x, start_y - 40)
        self.pen.color(GREEN_COLOR)
        self.pen.write(f"Your Wins: {user_win}", align="left", font=("Google Sans Flex", 12, "normal"))
        
        # AI wins
        self.pen.penup()
        self.pen.goto(left_x, start_y - 80)
        self.pen.color(RED_COLOR)
        self.pen.write(f"AI Wins: {ai_win}", align="left", font=("Google Sans Flex", 12, "normal"))
        
        # Computer's turn indicator
        if not self.player_turn and not self.game_ended:
            self.pen.penup()
            self.pen.goto(0, WIN_H/2 - 60)
            self.pen.color(ORANGE_COLOR)
            self.pen.write("Computer's Turn...", align="center", font=("Google Sans Flex", 20, "bold"))
    
    def draw_paused_overlay(self):
        # Semi-transparent effect - just draw text
        self.pen.penup()
        self.pen.goto(0, WIN_H/2 - 60)
        self.pen.color("white")
        self.pen.write("Paused - Press >Esc< to resume", align="center", font=("Google Sans Flex", 24, "bold"))
    
    def draw_game_over(self):
        # Draw the board first
        self.draw_board()
        
        # Draw overlay effect with text
        self.pen.penup()
        self.pen.goto(0, 150)
        
        if self.winner == Cell.EMPTY:
            self.pen.color(200/255, 200/255, 200/255)
            self.pen.write("IT'S A DRAW!", align="center", font=("Google Sans Flex", 48, "bold"))
            self.pen.goto(0, WIN_H/2 - 60)
            self.pen.color("white")
            self.pen.write("The board is full - no winner this time", align="center", font=("Google Sans Flex", 20, "normal"))
        elif self.winner == self.human_color:
            self.pen.color(GREEN_COLOR)
            self.pen.write("VICTORY!", align="center", font=("Google Sans Flex", 48, "bold"))
            self.pen.penup()
            self.pen.goto(0, WIN_H/2 - 60)
            self.pen.color("white")
            self.pen.write("You defeated the computer!", align="center", font=("Google Sans Flex", 20, "normal"))
        else:
            self.pen.color(RED_COLOR)
            self.pen.write("DEFEAT", align="center", font=("Google Sans Flex", 48, "bold"))
            self.pen.penup()
            self.pen.goto(-400, WIN_H/2 - 60)
            self.pen.color("red")
            self.pen.write("The computer wins this round", align="center", font=("Google Sans Flex", 12, "normal"))
        
        # Draw buttons
        self.new_game_btn.draw(self.pen)
        self.main_menu_btn.draw(self.pen)
    
    def run(self):
        self.screen.mainloop()

# Main entry point
if __name__ == "__main__":
    game = GomokuGame()
    game.run()
