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
MAX_DEPTH = 6

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

# Transposition table for AI with Zobrist Hashing
class TranspositionTable:
    def __init__(self):
        self.cache = {}
        # Initialize Zobrist hash table for faster hashing
        random.seed(42)
        self.zobrist = [[[random.getrandbits(64) for _ in range(3)] 
                         for _ in range(BOARD_SIZE)] 
                        for _ in range(BOARD_SIZE)]
    
    def compute_hash(self, board):
        """Compute Zobrist hash for board state - O(n²) but only called once"""
        h = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = board[r * BOARD_SIZE + c]
                if piece != Cell.EMPTY:
                    h ^= self.zobrist[r][c][piece]
        return h
    
    def contains(self, hash_key):
        return hash_key in self.cache
    
    def get(self, hash_key):
        entry = self.cache.get(hash_key)
        return entry if entry is not None else None
    
    def set(self, hash_key, value, depth):
        # Store with depth for better replacement strategy
        if hash_key not in self.cache or self.cache[hash_key][1] <= depth:
            self.cache[hash_key] = (value, depth)
    
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
        self.last_move = None  # Track last move for optimized win checking
        
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
        self.last_move = None
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
        """Optimized win checking - check all positions but with early exit"""
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
    
    def check_win_fast(self, board_state, player, last_r, last_c):
        """Fast win checking - only check around last move"""
        if last_r is None or last_c is None:
            return self.check_win(board_state, player)
        
        # Check horizontal
        count = 1
        # Check left
        c = last_c - 1
        while c >= 0 and board_state[self.index(last_r, c)] == player:
            count += 1
            c -= 1
        # Check right
        c = last_c + 1
        while c < BOARD_SIZE and board_state[self.index(last_r, c)] == player:
            count += 1
            c += 1
        if count >= WIN_LENGTH:
            return True
        
        # Check vertical
        count = 1
        # Check up
        r = last_r - 1
        while r >= 0 and board_state[self.index(r, last_c)] == player:
            count += 1
            r -= 1
        # Check down
        r = last_r + 1
        while r < BOARD_SIZE and board_state[self.index(r, last_c)] == player:
            count += 1
            r += 1
        if count >= WIN_LENGTH:
            return True
        
        # Check diagonal (\)
        count = 1
        # Check up-left
        r, c = last_r - 1, last_c - 1
        while r >= 0 and c >= 0 and board_state[self.index(r, c)] == player:
            count += 1
            r -= 1
            c -= 1
        # Check down-right
        r, c = last_r + 1, last_c + 1
        while r < BOARD_SIZE and c < BOARD_SIZE and board_state[self.index(r, c)] == player:
            count += 1
            r += 1
            c += 1
        if count >= WIN_LENGTH:
            return True
        
        # Check anti-diagonal (/)
        count = 1
        # Check up-right
        r, c = last_r - 1, last_c + 1
        while r >= 0 and c < BOARD_SIZE and board_state[self.index(r, c)] == player:
            count += 1
            r -= 1
            c += 1
        # Check down-left
        r, c = last_r + 1, last_c - 1
        while r < BOARD_SIZE and c >= 0 and board_state[self.index(r, c)] == player:
            count += 1
            r += 1
            c -= 1
        if count >= WIN_LENGTH:
            return True
        
        return False
    
    def count_threat_level(self, board_state, player, r, c):
        """Count how many pieces in a line and if it's open - returns threat level"""
        if board_state[self.index(r, c)] != Cell.EMPTY:
            return 0
        
        max_threat = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # horizontal, vertical, diagonal, anti-diagonal
        
        for dr, dc in directions:
            count = 0
            open_ends = 0
            
            # Count in positive direction
            pos_count = 0
            for i in range(1, 5):
                nr, nc = r + i * dr, c + i * dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board_state[self.index(nr, nc)] == player:
                        pos_count += 1
                    elif board_state[self.index(nr, nc)] == Cell.EMPTY:
                        open_ends += 1
                        break
                    else:
                        break
                else:
                    break
            
            # Count in negative direction
            neg_count = 0
            for i in range(1, 5):
                nr, nc = r - i * dr, c - i * dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board_state[self.index(nr, nc)] == player:
                        neg_count += 1
                    elif board_state[self.index(nr, nc)] == Cell.EMPTY:
                        open_ends += 1
                        break
                    else:
                        break
                else:
                    break
            
            count = pos_count + neg_count
            
            # Evaluate threat level
            if count >= 4:
                return 10000  # Immediate win/block
            elif count == 3:
                if open_ends == 2:
                    max_threat = max(max_threat, 5000)  # Open three - very dangerous
                elif open_ends == 1:
                    max_threat = max(max_threat, 1000)  # Semi-open three
            elif count == 2:
                if open_ends == 2:
                    max_threat = max(max_threat, 500)  # Open two
                elif open_ends == 1:
                    max_threat = max(max_threat, 100)  # Semi-open two
        
        return max_threat
    
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
        """Optimized board evaluation with early termination"""
        opponent = Cell.BLACK if ai_player == Cell.WHITE else Cell.WHITE
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
                            score += 50000
                        elif ai_count == 3:
                            score += 5000
                        elif ai_count == 2:
                            score += 500
                        elif ai_count == 1:
                            score += 50
                    
                    if ai_count == 0:
                        if opponent_count >= 4:
                            score -= 50000
                        elif opponent_count == 3:
                            score -= 5000
                        elif opponent_count == 2:
                            score -= 500
                        elif opponent_count == 1:
                            score -= 50
                
                # Early termination if clearly winning/losing
                if abs(score) > 100000:
                    return score
        
        return score
    
    def minimax(self, board_state, depth, alpha, beta, is_maximizing, ai_player):
        # Compute hash for caching
        board_hash = self.tt.compute_hash(board_state)
        
        # Check cache with improved depth awareness
        if depth < MAX_DEPTH - 2:
            cached = self.tt.get(board_hash)
            if cached is not None and cached[1] >= depth:
                return cached[0]
        
        opponent = Cell.WHITE if ai_player == Cell.BLACK else Cell.BLACK
        
        # Terminal conditions
        if self.check_win(board_state, ai_player):
            return 1000000 - depth
        if self.check_win(board_state, opponent):
            return -1000000 + depth
        if depth == 0 or all(cell != Cell.EMPTY for cell in board_state):
            eval_score = self.evaluate_board(board_state, ai_player)
            if depth < MAX_DEPTH - 2:
                self.tt.set(board_hash, eval_score, depth)
            return eval_score
        
        possible_moves = self.generate_candidate_moves(board_state)
        self.sort_moves_by_priority(possible_moves, board_state, ai_player)
        
        # Reduce branching for deeper searches
        max_moves = 20 if depth > 2 else 25
        if len(possible_moves) > max_moves:
            possible_moves = possible_moves[:max_moves]
        
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
                self.tt.set(board_hash, max_eval, depth)
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
                self.tt.set(board_hash, min_eval, depth)
            return min_eval
    
    def sort_moves_by_priority(self, moves, board_state, ai_player):
        opponent = Cell.WHITE if ai_player == Cell.BLACK else Cell.BLACK
        
        def get_priority(move):
            priority = 0
            r, c = move[0], move[1]
            
            # Check for immediate win (in-place modification)
            board_state[self.index(r, c)] = ai_player
            if self.check_win_fast(board_state, ai_player, r, c):
                priority += 100000
            board_state[self.index(r, c)] = Cell.EMPTY
            
            # Check for blocking opponent win (in-place modification)
            board_state[self.index(r, c)] = opponent
            if self.check_win_fast(board_state, opponent, r, c):
                priority += 90000
            board_state[self.index(r, c)] = Cell.EMPTY
            
            # Check threat level for AI's move
            ai_threat = self.count_threat_level(board_state, ai_player, r, c)
            priority += ai_threat
            
            # Check threat level we're blocking (more important)
            opponent_threat = self.count_threat_level(board_state, opponent, r, c)
            priority += opponent_threat * 1.5  # Blocking is slightly more important
            
            # Center distance priority
            center_dist = abs(r - BOARD_SIZE//2) + abs(c - BOARD_SIZE//2)
            priority += (BOARD_SIZE - center_dist) * 5
            
            return priority
        
        moves.sort(key=get_priority, reverse=True)
    
    def get_best_move(self, board_state, ai_player):
        best_move = (-1, -1)
        best_score = float('-inf')
        opponent = Cell.WHITE if ai_player == Cell.BLACK else Cell.BLACK
        
        # Check for immediate win (optimized with fast check)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board_state[self.index(r, c)] == Cell.EMPTY:
                    board_state[self.index(r, c)] = ai_player
                    if self.check_win_fast(board_state, ai_player, r, c):
                        best_move = (r, c)
                        board_state[self.index(r, c)] = Cell.EMPTY
                        return best_move
                    board_state[self.index(r, c)] = Cell.EMPTY
        
        # Check for blocking immediate win
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board_state[self.index(r, c)] == Cell.EMPTY:
                    board_state[self.index(r, c)] = opponent
                    if self.check_win_fast(board_state, opponent, r, c):
                        best_move = (r, c)
                        board_state[self.index(r, c)] = Cell.EMPTY
                        return best_move
                    board_state[self.index(r, c)] = Cell.EMPTY
        
        # Check for critical threats (open 3s and 4s)
        max_threat = 0
        threat_move = (-1, -1)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board_state[self.index(r, c)] == Cell.EMPTY:
                    # Check opponent's threat at this position
                    threat_level = self.count_threat_level(board_state, opponent, r, c)
                    if threat_level > max_threat:
                        max_threat = threat_level
                        threat_move = (r, c)
        
        # If there's a serious threat (open 3 or more), block it immediately
        if max_threat >= 5000:
            return threat_move
        
        # Use minimax
        possible_moves = self.generate_candidate_moves(board_state)
        self.sort_moves_by_priority(possible_moves, board_state, ai_player)
        
        if len(possible_moves) > 15:
            possible_moves = possible_moves[:15]
        
        alpha = float('-inf')
        beta = float('inf')
        
        for move in possible_moves:
            board_state[self.index(move[0], move[1])] = ai_player
            score = self.minimax(board_state, MAX_DEPTH - 3, alpha, beta, False, ai_player)
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
            self.last_move = best_move
            
            if self.check_win_fast(self.board, self.computer_color, best_move[0], best_move[1]):
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
                    self.last_move = (r, c)
                    
                    if self.check_win_fast(self.board, self.human_color, r, c):
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
            self.pen.goto(0, WIN_H/2 - 50)
            self.pen.color(BLACK_COLOR)
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
