"""
This class is responsible for storing all the information about the current state of a chess game. It will also be
responsible for determining the valid moves at current state. It will also keep a move log
"""


class GameState:
    def __init__(self):
        # board is an 8x8 2d list, each element of the list has 2 characters,
        # The first character represents the color of the piece, 'b' or 'w'
        # The second character represents the type of piece
        # '--' - represents an empty space with no piece
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]
        self.move_functions = {
            "p": self.get_pawn_moves,
            "R": self.get_rook_moves,
            "N": self.get_knight_moves,
            "B": self.get_bishop_moves,
            "Q": self.get_queen_moves,
            "K": self.get_king_moves,
        }
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False

        self.in_check = False
        self.pins = []
        self.checks = []

    def make_move(self, move):
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move
        # update king's location if moved
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

    def undo_move(self):
        if self.move_log:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move
            # update king's location if moved
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)

    def get_valid_moves(self):
        moves = []
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()
        if self.white_to_move:
            king_row, king_col = self.white_king_location
        else:
            king_row, king_col = self.black_king_location
        if self.in_check:
            if len(self.checks) == 1:  # only 1 check, block check or move king
                moves = self.get_all_possible_moves()
                # to block a check you must move a piece into tne of the squares between the enemy piece and king
                check = self.checks[0]
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][
                    check_col
                ]  # enemy piece causing the check
                valid_squares = []  # squares that pieces can move to
                # if knight, must capture or move king, other pieces can be blocked
                if piece_checking[1] == "N":
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (
                            king_row + check[2] * i,
                            king_col + check[3] * i,
                        )  # check[2] and check[3] are the check directions
                        valid_squares.append(valid_square)
                        if (
                            valid_square[0] == check_row
                            and valid_square[1] == check_col
                        ):  # once you get to piece end checks
                            break
                # get rid of any moves that don't block check or move king
                for i in range(len(moves) -1, -1, -1):
                    if (
                        moves[i].piece_moved[1] != "K"
                    ):  # move doesn't move king so it must block or capture
                        if (
                            not (moves[i].end_row, moves[i].end_col) in valid_squares
                        ):  # move doesn't block check or capture
                            moves.remove(moves[i])
            else:  # double check, king has to move
                self.get_king_moves(king_row, king_col, moves)
        else:  # not in check so all moves are fine
            moves = self.get_all_possible_moves()

        return moves

    def check_for_pins_and_checks(self):
        pins = []  # squares where the allied pinned piece is and direction pinned from
        checks = []  # squares where enemy is applying a check
        in_check = False
        rock_moves = ((-1, 0), (0, -1), (1, 0), (0, 1))
        bishop_moves = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        white_pawn_moves = bishop_moves[0:2]
        black_pawn_moves = bishop_moves[2:4]
        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row, start_col = self.white_king_location
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row, start_col = self.black_king_location
        directions = rock_moves + bishop_moves
        for j in range(len(directions)):
            d = directions[j]
            possible_pin = ()  # reset possible pins
            for i in range(1, 8):
                end_row = start_row + d[0] * i
                end_col = start_col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":  # 1st allied piece could be pinned
                        if possible_pin == ():
                            possible_pin = (end_row, end_col, d[0], d[1])
                        else:  # 2nd allied piece, so no pin or check possible in this direction
                            break
                    elif end_piece[0] == enemy_color:
                        piece_type = end_piece[1]
                        # 5 possibilities here in this complex conditional
                        # 1.) orthogonally away from king and piece is a rock
                        # 2.) diagonally away from king and piece is a bishop
                        # 3.) 1 square away diagonally from king and piece is a pawn
                        # 4.) any direction and piece is a queen
                        # 5.) any direction 1 square away and piece is a king
                        # (this is necessary to prevent a king move to a square controlled by another king)
                        if (
                            (d in rock_moves and piece_type == "R")
                            or (d in bishop_moves and piece_type == "B")
                            or (
                                i == 1
                                and piece_type == "p"
                                and (
                                    (enemy_color == "w" and d in black_pawn_moves)
                                    or (enemy_color == "b" and d in white_pawn_moves)
                                )
                            )
                            or (piece_type == "Q")
                            or (i == 1 and piece_type == "K")
                        ):
                            if possible_pin == ():  # no piece blocking, so check
                                in_check = True
                                checks.append((end_row, end_col, d[0], d[1]))
                            else:  # piece blocking so pin
                                pins.append(possible_pin)
                                break
                        else:
                            break
                else:  # off board
                    break
        # check for knight checks
        # noinspection DuplicatedCode
        knight_moves = (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        )
        for m in knight_moves:
            end_row = start_row + m[0]
            end_col = start_col + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":
                    in_check = True
                    checks.append((end_row, end_col, m[0], m[1]))

        return in_check, pins, checks

    def get_valid_moves_old(self):
        print("white_to_move", self.white_to_move)
        # 1.) generate all possible moves
        moves = self.get_all_possible_moves()
        # 2.) for each move, make the move
        for i in range(len(moves) - 1, -1, -1):
            self.make_move(moves[i])
            # 3.) generate all opponent's moves
            # 4.) for each of your opponent's moves, see if they attack your king
            self.white_to_move = (
                not self.white_to_move
            )  # undo change turn made by make_move method
            if self.is_check():
                moves.remove(moves[i])  # 5.) if they attack your king, not a valid move
            self.white_to_move = not self.white_to_move
            self.undo_move()
        if len(moves) == 0:  # either checkmate or stalemate
            if self.is_check():
                self.checkmate = True
            else:
                self.stalemate = True

        return moves

    def is_check(self):
        if self.white_to_move:
            return self.square_under_attack(self.white_king_location)
        else:
            return self.square_under_attack(self.black_king_location)

    def square_under_attack(self, location):
        r, c = location
        self.white_to_move = not self.white_to_move  # switch to opponent's turn
        opponent_moves = self.get_all_possible_moves()
        self.white_to_move = not self.white_to_move  # switch turns back
        for move in opponent_moves:
            if move.end_row == r and move.end_col == c:
                return True

        return False

    def get_all_possible_moves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == "w" and self.white_to_move) or (
                    turn == "b" and not self.white_to_move
                ):
                    piece_type = self.board[r][c][1]
                    self.move_functions[piece_type](r, c, moves)

        return moves

    def get_pawn_moves(self, r, c, moves):
        piece_pinned = False
        pin_direction = ()
        start_square = (r, c)
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            if self.board[r - 1][c] == "--":  # 1 square pawn advance
                if not piece_pinned or pin_direction == (-1, 0):
                    moves.append(Move(start_square, (r - 1, c), self.board))
                    if r == 6 and self.board[r - 2][c] == "--":  # 2 square pawn advance
                        moves.append(Move((r, c), (r - 2, c), self.board))

            if c - 1 >= 0:  # capture to the left
                if self.board[r - 1][c - 1][0] == "b":  # enemy piece to capture
                    if not piece_pinned or pin_direction == (-1, -1):
                        moves.append(Move(start_square, (r - 1, c - 1), self.board))
            if c + 1 <= 7:  # capture to the right
                if self.board[r - 1][c + 1][0] == "b":  # enemy piece to capture
                    if not piece_pinned or pin_direction == (-1, 1):
                        moves.append(Move(start_square, (r - 1, c + 1), self.board))
        else:
            if self.board[r + 1][c] == "--":  # 1 square pawn advance
                if not piece_pinned or pin_direction == (1, 0):
                    moves.append(Move((r, c), (r + 1, c), self.board))
                    if r == 1 and self.board[r + 2][c] == "--":  # 2 square pawn advance
                        moves.append(Move((r, c), (r + 2, c), self.board))

            if c - 1 >= 0:  # capture to the left
                if self.board[r + 1][c - 1][0] == "w":  # enemy piece to capture
                    if not piece_pinned or pin_direction == (1, -1):
                        moves.append(Move(start_square, (r + 1, c - 1), self.board))
            if c + 1 <= 7:  # capture to the right
                if self.board[r + 1][c + 1][0] == "w":  # enemy piece to capture
                    if not piece_pinned or pin_direction == (1, 1):
                        moves.append(Move(start_square, (r + 1, c + 1), self.board))

    def get_rook_moves(self, r, c, moves):
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        self.calculate_moves_rook(r, c, directions, moves)

    def get_bishop_moves(self, r, c, moves):
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        self.calculate_moves_bishop(r, c, directions, moves)

    def get_queen_moves(self, r, c, moves):
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_knight_moves(self, r, c, moves):
        knight_moves = (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        )
        self.calculate_moves_knight(r, c, knight_moves, moves)

    def get_king_moves(self, r, c, moves):
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        start_square = (r, c)
        ally_color = self.get_ally_color()

        for i in range(8):
            end_row = r + row_moves[i]
            end_col = c + col_moves[i]
            end_square = (end_row, end_col)
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    if ally_color == 'w':
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.check_for_pins_and_checks()
                    if not in_check:
                        moves.append(Move(start_square, end_square, self.board))
                    if ally_color == 'w':
                        self.white_king_location = (r, c)
                    else:
                        self.black_king_location = (r, c)

    def get_enemy_color(self):
        enemy_color = "b" if self.white_to_move else "w"
        return enemy_color

    def calculate_moves_rook(self, r, c, directions, moves):
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if (
                    self.board[r][c][1] != "Q"
                ):  # can't remove queen from pin on rock moves, only remove it on bishop moves
                    self.pins.remove(self.pins[i])
                break

        start_square = (r, c)
        enemy_color = self.get_enemy_color()
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                end_square = (end_row, end_col)
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if (
                        not piece_pinned
                        or pin_direction == d
                        or pin_direction == (-d[0], -d[1])
                    ):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":
                            moves.append(Move(start_square, end_square, self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move(start_square, end_square, self.board))
                            break
                        else:  # friendly piece invalid
                            break
                else:  # off board
                    break

    def calculate_moves_bishop(self, r, c, directions, moves):
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        start_square = (r, c)
        enemy_color = self.get_enemy_color()
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                end_square = (end_row, end_col)
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if (
                        not piece_pinned
                        or pin_direction == d
                        or pin_direction == (-d[0], -d[1])
                    ):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":
                            moves.append(Move(start_square, end_square, self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move(start_square, end_square, self.board))
                            break
                        else:  # friendly piece invalid
                            break
                else:  # off board
                    break

    def get_ally_color(self):
        ally_color = "w" if self.white_to_move else "b"
        return ally_color

    def calculate_moves_knight(self, r, c, directions, moves):
        piece_pinned = False
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break
        start_square = (r, c)
        ally_color = self.get_ally_color()
        for m in directions:
            end_row = r + m[0]
            end_col = c + m[1]
            end_square = (end_row, end_col)
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:
                        moves.append(Move(start_square, end_square, self.board))


class Move:
    # maps keys to values
    # key: value
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        self.move_id = (
            self.start_row * 1000
            + self.start_col * 100
            + self.end_row * 10
            + self.end_col
        )

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False

    def get_chess_notation(self):
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(
            self.end_row, self.end_col
        )

    def get_rank_file(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]
