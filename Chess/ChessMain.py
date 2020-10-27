"""
This is our main driver file. It will be responsible for handling user input and displaying the current GameState object.
"""

import pygame as p
from Chess import ChessEngine

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}


def load_images():
    pieces = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(
            p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE)
        )


def draw_game_state(screen, gs, valid_moves, sq_selected):
    draw_board(screen)
    highlight_squares(screen, gs, valid_moves, sq_selected)
    draw_pieces(screen, gs.board)


def draw_board(screen):
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(
                screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            )


def draw_pieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(
                    IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
                )


def highlight_squares(screen, gs, valid_moves, sq_selected):
    if sq_selected != ():
        r, c = sq_selected
        if gs.board[r][c][0] == ("w" if gs.white_to_move else "b"):
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # transparency value -> 0 transparent; 255 opaque
            s.fill(p.Color("blue"))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

            s.fill((p.Color("yellow")))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    screen.blit(s, (move.end_col * SQ_SIZE, move.end_row * SQ_SIZE))


def animate_move(move, screen, board, clock):
    global colors
    delta_row = move.end_row - move.start_row
    delta_col = move.end_col = move.start_col

    frame_per_square = 10  # frames to move one square
    frame_count = (abs(delta_row) + abs(delta_col)) * frame_per_square
    for frame in range(frame_count + 1):
        r, c = (
            move.start_row + delta_row * frame / frame_count,
            move.start_col + delta_col * frame / frame_count,
        )
        draw_board(screen)
        draw_pieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(
            move.end_col * SQ_SIZE, move.end_row * SQ_SIZE, SQ_SIZE, SQ_SIZE
        )
        p.draw.rect(screen, color, end_square)
        # draw captured piece onto rectangle
        if move.piece_captured != "--":
            screen.blit(IMAGES[move.piece_captured], end_square)
        # draw moving piece
        screen.blit(
            IMAGES[move.piece_moved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        )
        p.display.flip()
        clock.tick(360)


def draw_text(screen, text):
    font = p.font.SysFont("Helvitca", 32, True, False)
    text_object = font.render(text, 0, p.Color("gray"))
    text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(
        WIDTH / 2 - text_object.get_width() / 2,
        HEIGHT / 2 - text_object.get_height() / 2,
    )
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, p.Color("darkgreen"))
    screen.blit(text_object, text_location.move(2, 2))


def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    load_images()
    running = True
    sq_selected = ()  # no square is selected, keep track of the last click of the user (tuple: (row, column))
    player_clicks = (
        []
    )  # keep track of player clicks (two tuples: [(row, column), (row, column)])
    valid_moves = gs.get_valid_moves()
    move_made = False  # flag variable for when move is made
    animate = False  # flag variable for when we should animate a move
    game_over = False

    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    if sq_selected == (
                        row,
                        col,
                    ):  # the user clicked the same square twice
                        sq_selected = ()
                        player_clicks = []
                    else:
                        sq_selected = (row, col)
                        player_clicks.append(sq_selected)

                    if len(player_clicks) == 2:
                        move = ChessEngine.Move(
                            player_clicks[0], player_clicks[1], gs.board
                        )
                        print(move.get_chess_notation())
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                gs.make_move(valid_moves[i])
                                move_made = True
                                animate = True
                                sq_selected = ()  # reset user clocks
                                player_clicks = []
                        if not move_made:
                            player_clicks = [sq_selected]
            # key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # undo when 'z' is pressed
                    gs.undo_move()
                    move_made = True
                    animate = False
                if e.key == p.K_r:  # reset the board when 'r is pressed
                    gs = ChessEngine.GameState()
                    valid_moves = gs.get_valid_moves()
                    sq_selected = ()
                    move_made = False
                    animate = False

        if move_made:
            animate = False  # TODO check animate method
            if animate:
                animate_move(gs.move_log[-1], screen, gs.board, clock)
            valid_moves = gs.get_valid_moves()
            move_made = False
            animate = False

        draw_game_state(screen, gs, valid_moves, sq_selected)
        if gs.checkmate:
            game_over = True
            if gs.white_to_move:
                draw_text(screen, "Black wins by checkmate")
            else:
                draw_text(screen, "White wins by checkmate")
        elif gs.stalemate:
            game_over = True
            draw_text(screen, "Stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()


if __name__ == "__main__":
    main()
