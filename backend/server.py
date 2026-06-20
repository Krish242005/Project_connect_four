from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class ConnectFourGame:
    def __init__(self):
        self.ROWS = 6
        self.COLS = 7
        self.board = self.create_empty_board()
        self.current_player = 'G'  # Green (Human) starts first
        self.game_over = False
        self.winner = None
        self.ai_strategy = 'balanced'
    
    def create_empty_board(self):
        """Create an empty 6x7 board"""
        return [[' ' for _ in range(self.COLS)] for _ in range(self.ROWS)]
    
    def reset_game(self, ai_strategy='balanced'):
        """Reset the game state"""
        self.board = self.create_empty_board()
        self.current_player = 'G'
        self.game_over = False
        self.winner = None
        self.ai_strategy = ai_strategy
    
    def make_move(self, col):
        """Make a move in the specified column"""
        # Validate the move
        if self.game_over:
            return False
        if col < 0 or col >= self.COLS:
            return False
        if self.board[0][col] != ' ':
            return False  # Column is full
        
        # Find the bottom-most empty row in the column
        for row in range(self.ROWS-1, -1, -1):
            if self.board[row][col] == ' ':
                self.board[row][col] = self.current_player
                
                # Check if this move wins the game
                if self.check_winner(row, col):
                    self.game_over = True
                    self.winner = self.current_player
                # Check if the board is full (draw)
                elif self.is_board_full():
                    self.game_over = True
                    self.winner = 'Draw'
                else:
                    # Switch to the other player
                    self.current_player = 'R' if self.current_player == 'G' else 'G'
                
                return True
        return False
    
    def check_winner(self, row, col):
        """Check if the current move wins the game"""
        player = self.board[row][col]
        
        # Check all four directions: horizontal, vertical, two diagonals
        directions = [
            [(0, 1), (0, -1)],   # horizontal
            [(1, 0), (-1, 0)],   # vertical
            [(1, 1), (-1, -1)],  # diagonal \
            [(1, -1), (-1, 1)]   # diagonal /
        ]
        
        for dir_pair in directions:
            count = 1  # Start with the current piece
            
            # Check both directions in each pair
            for dx, dy in dir_pair:
                current_row, current_col = row + dx, col + dy
                
                # Count consecutive pieces in this direction
                while (0 <= current_row < self.ROWS and 
                       0 <= current_col < self.COLS and 
                       self.board[current_row][current_col] == player):
                    count += 1
                    current_row += dx
                    current_col += dy
                    
                    if count >= 4:
                        return True
        
        return False
    
    def is_board_full(self):
        """Check if the board is completely filled"""
        return all(cell != ' ' for row in self.board for cell in row)
    
    def get_available_moves(self):
        """Get list of columns that are not full"""
        return [col for col in range(self.COLS) if self.board[0][col] == ' ']
    
    def get_computer_move(self):
        """Get the computer's move based on current strategy"""
        available_moves = self.get_available_moves()
        if not available_moves:
            return -1
        
        # Strategy 1: Win immediately if possible
        for col in available_moves:
            if self.is_winning_move(col, 'R'):
                return col
        
        # Strategy 2: Block opponent from winning
        for col in available_moves:
            if self.is_winning_move(col, 'G'):
                return col
        
        # Strategy 3: Use selected AI strategy
        if self.ai_strategy == 'novice':
            return self.novice_strategy(available_moves)
        elif self.ai_strategy == 'balanced':
            return self.balanced_strategy(available_moves)
        elif self.ai_strategy == 'strategist':
            return self.strategist_strategy(available_moves)
        else:  # master
            return self.master_strategy(available_moves)
    
    def is_winning_move(self, col, player):
        """Check if moving in this column would win the game"""
        # Find where the piece would land
        for row in range(self.ROWS-1, -1, -1):
            if self.board[row][col] == ' ':
                # Simulate the move
                self.board[row][col] = player
                is_win = self.check_winner(row, col)
                # Undo the move
                self.board[row][col] = ' '
                return is_win
        return False
    
    def evaluate_position(self, player):
        """Evaluate the current board position for the given player"""
        score = 0
        opponent = 'G' if player == 'R' else 'R'
        
        # Prefer center columns
        center_col = self.COLS // 2
        for row in range(self.ROWS):
            if self.board[row][center_col] == player:
                score += 3
        
        # Evaluate all possible lines of 4 cells
        # Horizontal lines
        for row in range(self.ROWS):
            for col in range(self.COLS - 3):
                line = [self.board[row][col+i] for i in range(4)]
                score += self.evaluate_line(line, player, opponent)
        
        # Vertical lines
        for row in range(self.ROWS - 3):
            for col in range(self.COLS):
                line = [self.board[row+i][col] for i in range(4)]
                score += self.evaluate_line(line, player, opponent)
        
        # Diagonal lines (\)
        for row in range(self.ROWS - 3):
            for col in range(self.COLS - 3):
                line = [self.board[row+i][col+i] for i in range(4)]
                score += self.evaluate_line(line, player, opponent)
        
        # Diagonal lines (/)
        for row in range(self.ROWS - 3):
            for col in range(3, self.COLS):
                line = [self.board[row+i][col-i] for i in range(4)]
                score += self.evaluate_line(line, player, opponent)
        
        return score
    
    def evaluate_line(self, line, player, opponent):
        """Evaluate a single line of 4 cells"""
        player_count = line.count(player)
        opponent_count = line.count(opponent)
        empty_count = line.count(' ')
        
        if player_count == 4:
            return 1000  # Win
        elif player_count == 3 and empty_count == 1:
            return 100   # 3 in a row
        elif player_count == 2 and empty_count == 2:
            return 10    # 2 in a row
        elif opponent_count == 3 and empty_count == 1:
            return -500  # Block opponent
        elif opponent_count == 2 and empty_count == 2:
            return -50   # Block opponent's 2 in a row
        
        return 0
    
    def novice_strategy(self, available_moves):
        """Easy AI: Random moves with slight center preference"""
        # Prefer center column 30% of the time
        if 3 in available_moves and random.random() < 0.3:
            return 3
        return random.choice(available_moves)
    
    def balanced_strategy(self, available_moves):
        """Medium AI: Balanced offense and defense"""
        best_score = -float('inf')
        best_moves = []
        
        for col in available_moves:
            # Simulate this move
            row = self.simulate_move(col, 'R')
            if row == -1:
                continue
            
            # Evaluate the position
            score = self.evaluate_position('R')
            
            # Prefer center columns
            if col == 3:
                score += 20
            elif col in [2, 4]:
                score += 10
            
            # Update best move
            if score > best_score:
                best_score = score
                best_moves = [col]
            elif score == best_score:
                best_moves.append(col)
            
            # Undo the simulated move
            self.undo_move(col)
        
        return random.choice(best_moves) if best_moves else random.choice(available_moves)
    
    def strategist_strategy(self, available_moves):
        """Hard AI: More strategic play"""
        best_score = -float('inf')
        best_moves = []
        
        for col in available_moves:
            row = self.simulate_move(col, 'R')
            if row == -1:
                continue
            
            # More sophisticated evaluation
            offensive_score = self.evaluate_position('R') * 2
            defensive_score = -self.evaluate_position('G') * 1.5
            total_score = offensive_score + defensive_score
            
            # Strong center preference
            if col == 3:
                total_score += 15
            elif col in [2, 4]:
                total_score += 8
            
            if total_score > best_score:
                best_score = total_score
                best_moves = [col]
            elif total_score == best_score:
                best_moves.append(col)
            
            self.undo_move(col)
        
        return random.choice(best_moves) if best_moves else random.choice(available_moves)
    
    def master_strategy(self, available_moves):
        """Expert AI: Very strategic play"""
        best_score = -float('inf')
        best_moves = []
        
        for col in available_moves:
            row = self.simulate_move(col, 'R')
            if row == -1:
                continue
            
            # Deep evaluation
            base_score = self.evaluate_position('R') * 3
            block_score = -self.evaluate_position('G') * 2
            
            # Positional advantage
            positional_score = 0
            if col == 3:
                positional_score += 25
            elif col in [2, 4]:
                positional_score += 12
            
            total_score = base_score + block_score + positional_score
            
            if total_score > best_score:
                best_score = total_score
                best_moves = [col]
            elif total_score == best_score:
                best_moves.append(col)
            
            self.undo_move(col)
        
        return random.choice(best_moves) if best_moves else random.choice(available_moves)
    
    def simulate_move(self, col, player):
        """Simulate a move and return the row where piece lands"""
        for row in range(self.ROWS-1, -1, -1):
            if self.board[row][col] == ' ':
                self.board[row][col] = player
                return row
        return -1
    
    def undo_move(self, col):
        """Undo a move in the specified column"""
        for row in range(self.ROWS):
            if self.board[row][col] != ' ':
                self.board[row][col] = ' '
                return

# Create a global game instance
game = ConnectFourGame()

# ==================== ROUTES ====================

@app.route('/')
def home():
    """Home route - test if server is running"""
    return jsonify({
        "message": "🎮 Connect Four Server is RUNNING!",
        "status": "success",
        "players": "Human (🟢 Green) vs Computer (🔴 Red)",
        "instructions": "Open frontend/index.html in your browser"
    })

@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    """Get current game state"""
    return jsonify({
        'success': True,
        'board': game.board,
        'current_player': game.current_player,
        'game_over': game.game_over,
        'winner': game.winner,
        'ai_strategy': game.ai_strategy
    })

@app.route('/api/game/move', methods=['POST'])
def make_move():
    """Make a player move"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        col = data.get('column')
        if col is None:
            return jsonify({'success': False, 'error': 'No column provided'}), 400
        
        # Make the move
        if game.make_move(col):
            return jsonify({
                'success': True,
                'board': game.board,
                'current_player': game.current_player,
                'game_over': game.game_over,
                'winner': game.winner
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid move - column may be full'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/game/computer/move', methods=['POST'])
def computer_move():
    """Make a computer move"""
    try:
        col = game.get_computer_move()
        if col != -1 and game.make_move(col):
            return jsonify({
                'success': True,
                'column': col,
                'board': game.board,
                'current_player': game.current_player,
                'game_over': game.game_over,
                'winner': game.winner
            })
        return jsonify({'success': False, 'error': 'No valid computer move available'}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Computer move error: {str(e)}'}), 500

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    """Reset the game"""
    try:
        data = request.get_json() or {}
        ai_strategy = data.get('ai_strategy', 'balanced')
        
        # Validate AI strategy
        valid_strategies = ['novice', 'balanced', 'strategist', 'master']
        if ai_strategy not in valid_strategies:
            ai_strategy = 'balanced'
        
        game.reset_game(ai_strategy)
        return jsonify({
            'success': True,
            'board': game.board,
            'current_player': game.current_player,
            'game_over': game.game_over,
            'winner': game.winner,
            'ai_strategy': game.ai_strategy
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Reset error: {str(e)}'}), 500

@app.route('/api/game/strategies', methods=['GET'])
def get_strategies():
    """Get available AI strategies"""
    return jsonify({
        'success': True,
        'strategies': [
            {'id': 'novice', 'name': 'NOVICE', 'description': 'Easy opponent - good for beginners'},
            {'id': 'balanced', 'name': 'BALANCED', 'description': 'Fair challenge - balanced play'},
            {'id': 'strategist', 'name': 'STRATEGIST', 'description': 'Hard opponent - strategic play'},
            {'id': 'master', 'name': 'MASTER', 'description': 'Expert level - very difficult'}
        ]
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Connect Four Game Server',
        'timestamp': 'Server is running correctly'
    })

# ==================== START SERVER ====================

if __name__ == '__main__':
    port = 5000
    
    print("=" * 50)
    print("🎮 CONNECT FOUR GAME SERVER")
    print("=" * 50)
    print(f"📍 Server URL: http://localhost:{port}")
    print("🟢 Human Player: GREEN discs")
    print("🔴 Computer: RED discs")
    print("⚡ Computer moves automatically after you")
    print("🎯 Click column numbers 1-7 to play")
    print("=" * 50)
    print("Starting server...")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Try using a different port: change 'port = 5000' to 'port = 5001'")