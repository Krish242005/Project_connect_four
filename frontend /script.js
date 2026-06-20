class ConnectFourGame {
    constructor() {
        this.baseUrl = 'http://localhost:5000/api';
        this.boardElement = document.getElementById('game-board');
        this.currentPlayerToken = document.getElementById('current-player-token');
        this.currentPlayerName = document.getElementById('current-player-name');
        this.gameStatusElement = document.getElementById('game-status');
        this.resetBtn = document.getElementById('reset-btn');
        this.computerBtn = document.getElementById('computer-btn');
        this.aiStrategySelect = document.getElementById('ai-strategy');
        
        this.isConnected = false;
        
        this.init();
    }
    
    async init() {
        this.createBoard();
        this.setupEventListeners();
        await this.testConnection();
    }
    
    async testConnection() {
        try {
            console.log('🔗 Testing connection to:', this.baseUrl);
            const response = await fetch(`${this.baseUrl}/game/state`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.isConnected = true;
                this.updateUI(data);
                this.showTemporaryMessage('✅ Connected to server! Ready to play.', 'var(--human-green)');
                console.log('✅ Server connection successful');
            } else {
                throw new Error(`Server responded with status: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Connection failed:', error);
            this.isConnected = false;
            this.gameStatusElement.textContent = '❌ Server not running. Start backend first!';
            this.gameStatusElement.style.color = 'var(--computer-red)';
            
            // Show detailed instructions
            setTimeout(() => {
                this.showTemporaryMessage('💡 Run: python server.py in backend folder', 'var(--computer-red)');
            }, 2000);
        }
    }
    
    createBoard() {
        this.boardElement.innerHTML = '';
        for (let row = 0; row < 6; row++) {
            for (let col = 0; col < 7; col++) {
                const cell = document.createElement('div');
                cell.className = 'cell empty';
                cell.dataset.row = row;
                cell.dataset.col = col;
                this.boardElement.appendChild(cell);
            }
        }
    }
    
    setupEventListeners() {
        // Column headers for dropping pieces
        document.querySelectorAll('.column-header').forEach(header => {
            header.addEventListener('click', (e) => {
                if (this.isGameActive()) {
                    const col = parseInt(e.target.dataset.column);
                    this.makeMove(col);
                }
            });
        });
        
        // Reset button
        this.resetBtn.addEventListener('click', () => {
            this.resetGame();
        });
        
        // Computer move button (manual trigger - optional)
        this.computerBtn.addEventListener('click', () => {
            if (this.isGameActive()) {
                this.makeComputerMove();
            }
        });
        
        // AI strategy change
        this.aiStrategySelect.addEventListener('change', (e) => {
            this.changeAIStrategy(e.target.value);
        });
    }
    
    isGameActive() {
        if (!this.isConnected) {
            this.showTemporaryMessage('Server not connected!', 'var(--computer-red)');
            return false;
        }
        
        const status = this.gameStatusElement.textContent;
        return !status.includes('wins') &&
               !status.includes('DRAW') &&
               !status.includes('VICTORY') &&
               !status.includes('Error');
    }
    
    async makeMove(column) {
        if (!this.isConnected) {
            this.showTemporaryMessage('Not connected to server!', 'var(--computer-red)');
            return;
        }
        
        try {
            console.log('Making move in column:', column);
            const response = await fetch(`${this.baseUrl}/game/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ column: column })
            });
            
            const result = await response.json();
            console.log('Move response:', result);
            
            if (result.success) {
                this.updateUI(result);
                
                // AUTOMATIC COMPUTER MOVE: If game is not over and it's computer's turn
                if (!result.game_over && result.current_player === 'R') {
                    setTimeout(() => this.makeComputerMove(), 1000);
                }
            } else {
                this.showTemporaryMessage(result.error || 'Invalid move!', 'var(--computer-red)');
            }
        } catch (error) {
            console.error('Move error:', error);
            this.showTemporaryMessage('Connection lost! Check server.', 'var(--computer-red)');
            this.isConnected = false;
        }
    }
    
    async makeComputerMove() {
        if (!this.isConnected) return;
        
        try {
            this.computerBtn.disabled = true;
            this.computerBtn.textContent = 'THINKING...';
            this.gameStatusElement.textContent = 'COMPUTER IS THINKING...';
            
            console.log('Requesting computer move...');
            const response = await fetch(`${this.baseUrl}/game/computer/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            console.log('Computer move response:', result);
            
            if (result.success) {
                this.updateUI(result);
                this.highlightComputerMove(result.column);
            } else {
                this.showTemporaryMessage(result.error || 'Computer move failed', 'var(--computer-red)');
            }
        } catch (error) {
            console.error('Computer move error:', error);
            this.showTemporaryMessage('Computer move failed!', 'var(--computer-red)');
        } finally {
            this.computerBtn.disabled = false;
            this.computerBtn.textContent = 'COMPUTER MOVE';
        }
    }
    
    highlightComputerMove(column) {
        const headers = document.querySelectorAll('.column-header');
        if (headers[column]) {
            headers[column].style.background = 'linear-gradient(135deg, var(--computer-red), var(--computer-red-dark))';
            headers[column].style.color = 'var(--parchment)';
            
            setTimeout(() => {
                headers[column].style.background = '';
                headers[column].style.color = '';
            }, 1000);
        }
    }
    
    async changeAIStrategy(strategy) {
        if (!this.isConnected) {
            this.showTemporaryMessage('Not connected to server!', 'var(--computer-red)');
            return;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/game/reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ai_strategy: strategy })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.updateUI(result);
                
                const strategyNames = {
                    'novice': 'NOVICE',
                    'balanced': 'BALANCED',
                    'strategist': 'STRATEGIST',
                    'master': 'MASTER'
                };
                
                this.showTemporaryMessage(`AI Level: ${strategyNames[strategy]}`, 'var(--gold)');
            }
        } catch (error) {
            this.showTemporaryMessage('Failed to change AI level', 'var(--computer-red)');
        }
    }
    
    async resetGame() {
        if (!this.isConnected) {
            this.showTemporaryMessage('Not connected to server!', 'var(--computer-red)');
            return;
        }
        
        try {
            const selectedStrategy = this.aiStrategySelect.value;
            const response = await fetch(`${this.baseUrl}/game/reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ai_strategy: selectedStrategy })
            });
            
            const result = await response.json();
            this.updateUI(result);
            this.showTemporaryMessage('New Game Started! You are Green.', 'var(--human-green)');
            
        } catch (error) {
            this.showTemporaryMessage('Failed to start new game', 'var(--computer-red)');
        }
    }
    
    updateUI(gameState) {
        console.log('Updating UI with:', gameState);
        
        // Update board with clear visibility
        const cells = document.querySelectorAll('.cell');
        gameState.board.forEach((row, rowIndex) => {
            row.forEach((cell, colIndex) => {
                const cellIndex = rowIndex * 7 + colIndex;
                if (cells[cellIndex]) {
                    cells[cellIndex].className = 'cell';
                    if (cell === 'G') {
                        cells[cellIndex].classList.add('human');
                    } else if (cell === 'R') {
                        cells[cellIndex].classList.add('computer');
                    } else {
                        cells[cellIndex].classList.add('empty');
                    }
                }
            });
        });
        
        // Update current player display
        if (gameState.current_player) {
            const isHumanTurn = gameState.current_player === 'G';
            const playerName = isHumanTurn ? 'HUMAN (GREEN)' : 'COMPUTER (RED)';
            const playerClass = isHumanTurn ? 'human' : 'computer';
            
            this.currentPlayerToken.innerHTML = `<div class="token ${playerClass}"></div>`;
            this.currentPlayerName.textContent = playerName;
        }
        
        // Update game status
        if (gameState.game_over) {
            if (gameState.winner === 'Draw') {
                this.gameStatusElement.textContent = "GAME ENDS IN A DRAW!";
                this.gameStatusElement.style.color = 'var(--silver)';
            } else {
                const winnerName = gameState.winner === 'G' ? '🎉 YOU WIN! 🎉' : 'COMPUTER WINS!';
                this.gameStatusElement.textContent = winnerName;
                this.gameStatusElement.style.color = gameState.winner === 'G' ? 'var(--human-green)' : 'var(--computer-red)';
                
                // Add winning animation
                this.highlightWinningPieces();
            }
        } else if (gameState.current_player) {
            const turnMessage = gameState.current_player === 'G' ? 'YOUR TURN - CLICK A COLUMN' : 'COMPUTER IS THINKING...';
            this.gameStatusElement.textContent = turnMessage;
            this.gameStatusElement.style.color = gameState.current_player === 'G' ? 'var(--human-green)' : 'var(--computer-red)';
        }
    }
    
    highlightWinningPieces() {
        setTimeout(() => {
            const pieces = document.querySelectorAll('.cell.human, .cell.computer');
            pieces.forEach(piece => {
                piece.classList.add('winning-piece');
            });
        }, 500);
    }
    
    showTemporaryMessage(message, color = 'var(--gold)') {
        const originalMessage = this.gameStatusElement.textContent;
        const originalColor = this.gameStatusElement.style.color;
        
        this.gameStatusElement.textContent = message;
        this.gameStatusElement.style.color = color;
        
        setTimeout(() => {
            if (this.gameStatusElement.textContent === message) {
                this.gameStatusElement.textContent = originalMessage;
                this.gameStatusElement.style.color = originalColor;
            }
        }, 3000);
    }
}

// Initialize the game when page loads
document.addEventListener('DOMContentLoaded', () => {
    new ConnectFourGame();
});
