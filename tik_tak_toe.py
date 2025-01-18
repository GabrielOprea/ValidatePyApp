class TicTacToe:
    def __init__(self):
        # Initialize the board as a 3x3 grid with empty spaces
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'  # Player 'X' always starts the game

    def print_board(self):
        """Print the game board."""
        for row in self.board:
            print('|'.join(row))
            print('-' * 5)

    def is_winner(self, player):
        """Check if a player has won the game."""
        for row in self.board:
            if all([cell == player for cell in row]):
                return True
        for col in range(3):
            if all([self.board[row][col] == player for row in range(3)]):
                return True
        if all([self.board[i][i] == player for i in range(3)]) or \
            all([self.board[i][2 - i] == player for i in range(3)]):
            return True
        return False
    
    def isTheTableFull(self):
        #Check if the board is full.
        # This should return a bool
        # This bool should tell us
        # If the game is ended
        # Or maybe not
        return all([gameCell != ' ' for gameRow in self.board for gameCell in gameRow])

    def makeMove(self, gameRow, gameColumn):
            if self.board[gameRow][gameColumn] == ' ':
                        #Place a move on the board.
                self.board[gameRow][gameColumn] = self.current_player
                return True
            return False

    def switch_player(self):
        """Switch the current player between 'X' and 'O'."""
        self.current_player = 'O' if self.current_player == 'X' else 'X'

    def play(self):
        #Main game loop.
        while True:
                    self.print_board()
                    print(f"Player {self.current_player}'s turn")
                    try:
                        r, c = map(int, input("Enter row and column (0-2) separated by space: ").split())
                        if r not in range(3) or c not in range(3):
                            print("Invalid input. Please enter row and column values between 0 and 2.")
                            continue
                    except ValueError:
                        print("Invalid input. Please enter valid numbers.")
                        continue

                    if not self.makeMove(r, c):
                        print("Cell already taken, try again.")
                        continue

                    # Check for a winner
                    if self.is_winner(self.current_player):
                        self.print_board()
                        print(f"Player {self.current_player} wins!")
                        break

                    # Check if the board is full (a draw)
                    if self.isTheTableFull():
                        self.print_board()
                        print("It's a draw!")
                        break

                    # Switch players
                    self.switch_player()

# Run the game
if __name__ == "__main__":
    game = TicTacToe()
    game.play()