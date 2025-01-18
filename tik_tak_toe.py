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