import copy
import json
import queue
import threading

import PySimpleGUI as sg
import chess
import chess.engine
import chess.pgn
import cv2
from stockfish import Stockfish

from classes import Timer
from move_detector import MoveDetector
from server import init_server
from util import *


class EasyChessGui:
    queue = queue.Queue()
    is_p1_white = True  # White is at the bottom in board layout

    def __init__(self, theme):
        self.game = None
        self.theme = theme

        self.init_game()
        server_thread = threading.Thread(target=init_server, daemon=True)
        server_thread.start()

        self.psg_board = None
        self.menu_elem = None

        self.username = "P1"
        self.opp_id_name = "P2"

        self.human_base_time_ms = 5 * 60 * 1000  # 5 minutes
        self.human_inc_time_ms = 10 * 1000  # 10 seconds
        self.human_period_moves = 0
        self.human_tc_type = "fischer"

        self.engine_base_time_ms = 3 * 60 * 1000  # 5 minutes
        self.engine_inc_time_ms = 2 * 1000  # 10 seconds
        self.engine_period_moves = 0
        self.engine_tc_type = "fischer"

        # Default board color is brown
        self.sq_light_color = "#F0D9B5"
        self.sq_dark_color = "#B58863"

        # Move highlight, for brown board
        self.move_sq_light_color = "#E8E18E"
        self.move_sq_dark_color = "#B8AF4E"

        self.gui_theme = theme
        # self.bella = MoveDetector()
        self.bella = None

        # platform specific stockfish path
        if sys_os == "Windows":
            self.stockfish_path = "C:/Program Files/Stockfish/stockfish_13_win_x64_bmi2/stockfish_13_win_x64_bmi2.exe"
        elif sys_os == "Linux":
            self.stockfish_path = "/usr/games/stockfish"
        elif sys_os == "Darwin":
            self.stockfish_path = "/opt/homebrew/bin/stockfish"

        self.stockfish = Stockfish(path=self.stockfish_path)

    def get_move_from_to(self, user_move, move_cnt):
        print(user_move)
        p1 = user_move[0]
        p2 = user_move[1]

        if move_cnt % 2 == 0:
            correct = 'white'
        else:
            correct = 'black'

        p1_col = "abcdefgh".index(p1[0])
        p1_row = 8 - int(p1[1])
        piece1 = self.psg_board[p1_row][p1_col]

        p2_col = "abcdefgh".index(p2[0])
        p2_row = 8 - int(p2[1])
        piece2 = self.psg_board[p2_row][p2_col]

        if piece1 == 0:
            return p2, p1
        elif piece2 == 0:
            return p1, p2
        else:
            if piece1 <= 6 and correct == 'white':
                return p2, p1
            else:
                return p1, p2

    def update_game(self, mc: int, user_move: str, time_left: int):
        """Saves moves in the game.

        Args:
          mc: move count
          user_move: user's move
          time_left: time left
        """
        # Save user comment
        self.stockfish.make_moves_from_current_position([''.join(user_move)])
        evalU = self.stockfish.get_evaluation()
        wdl = self.stockfish.get_wdl_stats()
        best_move = self.stockfish.get_best_move()
        id = "black" if mc % 2 == 0 else "white"

        evaluation_dictionary.append(
            {"id": id, "move_count": (mc + 1) // 2 + 1, "best_move": best_move, "move": user_move, "wdl": wdl,
             "time_left": time_left, evalU['type']: evalU['value']})

    def create_new_window(self, window, flip=False):
        """Hide current window and creates a new window."""
        loc = window.CurrentLocation()
        window.Hide()
        if flip:
            self.is_p1_white = not self.is_p1_white

        layout = self.build_main_layout(self.is_p1_white)

        w = sg.Window("{} {}".format(APP_NAME, APP_VERSION), layout, default_button_element_size=(12, 1),
                      auto_size_buttons=False, location=(loc[0], loc[1]))

        # Initialize White and black boxes
        while True:
            button, value = w.Read(timeout=50)
            self.update_labels_and_game_tags(w, human=self.username)
            break

        window.Close()
        return w

    def get_time_mm_ss_ms(self, time_ms):
        """Returns time in min:sec:millisec given time in millisec"""
        s, ms = divmod(int(time_ms), 1000)
        m, s = divmod(s, 60)

        return "{:02d}:{:02d}".format(m, s)

    def get_time_h_mm_ss(self, time_ms, symbol=True):
        """
        Returns time in h:mm:ss format.

        :param time_ms:
        :param symbol:
        :return:
        """
        s, ms = divmod(int(time_ms), 1000)
        m, s = divmod(s, 60)

        if not symbol:
            return "{:02d}:{:02d}".format(m, s)
        return "{:02d}:{:02d}".format(m, s)

    def init_game(self):
        """Initialize game with initial pgn tag values"""
        self.game = chess.pgn.Game()

    def set_new_game(self):
        """Initialize new game but save old pgn tag values"""
        # Define a game object for saving game in pgn format
        self.game = chess.pgn.Game()

    def clear_elements(self, window):
        """Clear movelist, score, pv, time, depth and nps boxes"""
        window.find_element("_movelist_").update(disabled=False)
        window.find_element("_movelist_").update("", disabled=True)
        window.Element("w_base_time_k").update("")
        window.Element("b_base_time_k").update("")
        window.Element("w_elapse_k").update("")
        window.Element("b_elapse_k").update("")

    def update_labels_and_game_tags(self, window, human="Human"):
        """Update player names"""
        engine_id = self.opp_id_name
        if self.is_p1_white:
            window.find_element("_White_").update(human)
            window.find_element("_Black_").update(engine_id)
        else:
            window.find_element("_White_").update(engine_id)
            window.find_element("_Black_").update(human)

    def change_square_color(self, window, row, col):
        """
        Change the color of a square based on square row and col.
        """
        btn_sq = window.find_element(key=(row, col))
        is_dark_square = True if (row + col) % 2 else False
        bd_sq_color = (self.move_sq_dark_color if is_dark_square else self.move_sq_light_color)
        btn_sq.update(button_color=("white", bd_sq_color))

    def relative_row(self, s, stm):
        """
        The board can be viewed, as white at the bottom and black at the
        top. If stm is white the row 0 is at the bottom. If stm is black
        row 0 is at the top.
        :param s: square
        :param stm: side to move
        :return: relative row
        """
        return 7 - self.get_row(s) if stm else self.get_row(s)

    def get_row(self, s):
        """
        This row is based on PySimpleGUI square mapping that is 0 at the
        top and 7 at the bottom.
        In contrast Python-chess square mapping is 0 at the bottom and 7
        at the top. chess.square_rank() is a method from Python-chess that
        returns row given square s.

        :param s: square
        :return: row
        """
        return 7 - chess.square_rank(s)

    def get_col(self, s):
        """Returns col given square s"""
        return chess.square_file(s)

    def redraw_board(self, window):
        """
        Redraw board at start and afte a move.

        :param window:
        :return:
        """
        for i in range(8):
            for j in range(8):
                color = self.sq_dark_color if (i + j) % 2 else self.sq_light_color
                piece_image = images[self.psg_board[i][j]]
                elem = window.find_element(key=(i, j))
                elem.update(button_color=("white", color), image_filename=piece_image, )

    def render_square(self, image, key, location, label=None):
        """Returns an RButton (Read Button) with image image"""
        if (location[0] + location[1]) % 2:
            color = self.sq_dark_color  # Dark square
        else:
            color = self.sq_light_color
        return sg.RButton("", image_filename=image, size=(1, 1), border_width=0, button_color=("white", color),
                          pad=(0, 0), key=key, )

    def define_timer(self, window):
        """
        Returns Timer object for either human or engine.
        """
        timer = Timer(self.human_tc_type, self.human_base_time_ms, self.human_inc_time_ms, self.human_period_moves, )

        elapse_str = self.get_time_h_mm_ss(timer.base)
        window.Element("w_base_time_k").update(elapse_str)
        window.Element("b_base_time_k").update(elapse_str)

        return timer

    def play_game(self, window: sg.Window, board: chess.Board):
        """Play a game against an engine or human.

        Args:
          window: A PySimplegUI window.
          board: current board position
        """
        window.find_element("_movelist_").update(disabled=False)
        window.find_element("_movelist_").update("", disabled=True)

        move_cnt = 0

        # Init timer
        p1_timer = self.define_timer(window)
        p2_timer = self.define_timer(window)
        user_quit = False

        # Game loop
        while not board.is_game_over(claim_draw=True):
            if move_cnt % 2 == 0:
                timer = p1_timer
                if self.is_p1_white:
                    k1 = "w_elapse_k"
                    k2 = "w_base_time_k"
                else:
                    k1 = "b_elapse_k"
                    k2 = "b_base_time_k"
            else:
                timer = p2_timer
                if self.is_p1_white:
                    k1 = "b_elapse_k"
                    k2 = "b_base_time_k"
                else:
                    k1 = "w_elapse_k"
                    k2 = "w_base_time_k"
            while True:
                button, value = window.Read(timeout=100)

                if button is None:
                    user_quit = True
                    logging.info("Quit app from main loop, X is pressed.")
                    break

                # Update elapse box in m:s format
                elapse_str = self.get_time_mm_ss_ms(timer.elapse)
                window.Element(k1).update(elapse_str)
                timer.elapse += 100

                if button == "_moved_":
                    self.bella.takePicture()
                    user_move = self.bella.detectPiece()
                    move_from, move_to = self.get_move_from_to(user_move, move_cnt)
                    print(f"move_from: {move_from}, move_to: {move_to}")
                    save_to_json_file("evaluation.json", evaluation_dictionary)
                    if move_from is not None and move_to is not None and move_from != move_to:
                        break

            if user_quit:
                break

            fr_col = "abcdefgh".index(move_from[0])
            fr_row = 8 - int(move_from[1])
            piece = self.psg_board[fr_row][fr_col]

            self.change_square_color(window, fr_row, fr_col)

            to_col = "abcdefgh".index(move_to[0])
            to_row = 8 - int(move_to[1])

            # Empty the board from_square, applied to any types of move
            self.psg_board[fr_row][fr_col] = BLANK
            self.psg_board[to_row][to_col] = piece
            self.redraw_board(window)

            # Update clock, reset elapse to zero
            timer.update_base()

            # Update game, move from human
            time_left = timer.base
            self.update_game(move_cnt, move_from + move_to, time_left)

            if move_cnt % 2 == 0:
                window.find_element("_movelist_").update(f"{(move_cnt + 1) // 2 + 1}. ", append=True)
            window.find_element("_movelist_").update(disabled=False)
            window.find_element("_movelist_").update(f"{user_move} ", append=True)
            if move_cnt % 2 == 1:
                window.find_element("_movelist_").update("\n", append=True)

            # Change the color of the "fr" and "to" board squares
            self.change_square_color(window, fr_row, fr_col)
            self.change_square_color(window, to_row, to_col)

            # Update elapse box
            elapse_str = self.get_time_mm_ss_ms(timer.elapse)
            window.Element(k1).update(elapse_str)

            # Update remaining time box
            elapse_str = self.get_time_h_mm_ss(timer.base)
            window.Element(k2).update(elapse_str)

            move_cnt += 1

        if board.is_game_over(claim_draw=True):
            sg.Popup("Game is over.", title=BOX_TITLE)

        if not user_quit:
            self.clear_elements(window)
        return user_quit

    def create_board(self, is_p1_white=True):
        """
        Returns board layout based on color of user. If user is white,
        the white pieces will be at the bottom, otherwise at the top.

        :param is_p1_white: user has handling the white pieces
        :return: board layout
        """
        file_char_name = "abcdefgh"
        self.psg_board = copy.deepcopy(initial_board)

        board_layout = []

        if is_p1_white:
            # Save the board with black at the top.
            start = 0
            end = 8
            step = 1
        else:
            start = 7
            end = -1
            step = -1
            file_char_name = file_char_name[::-1]

        # Loop through the board and create buttons with images
        for i in range(start, end, step):
            # Row numbers at left of board is blank
            row = []
            for j in range(start, end, step):
                piece_image = images[self.psg_board[i][j]]
                row.append(self.render_square(piece_image, key=(i, j), location=(i, j)))
            board_layout.append(row)

        return board_layout

    def build_main_layout(self, is_p1_white=True):
        """
        Creates all elements for the GUI, including the board layout.

        :param is_p1_white: if user is white, the white pieces are
        oriented such that the white pieces are at the bottom.
        :return: GUI layout
        """
        sg.ChangeLookAndFeel(self.gui_theme)
        sg.SetOptions(margins=(0, 3), border_width=1)

        # Define board
        board_layout = self.create_board(is_p1_white)

        board_controls = [
            [sg.Text("Mode     Neutral", size=(36, 1), font=("Segoe UI", 10), key="_gamestatus_", visible=False, )], [
                sg.Text("Adviser", size=(7, 1), font=("Segoe UI", 10), key="adviser_k",
                        right_click_menu=["Right", ["Start::right_adviser_k", "Stop::right_adviser_k"], ],
                        visible=False, ),
                sg.Text("", font=("Segoe UI", 10), key="advise_info_k", relief="sunken", size=(46, 1),
                        visible=False, ), ], [
                sg.Multiline("", do_not_clear=True, autoscroll=False, size=(23, 4), font=("Segoe UI", 10),
                             key="polyglot_book1_k", visible=False, ),
                sg.Multiline("", do_not_clear=True, autoscroll=False, size=(25, 4), font=("Segoe UI", 10),
                             key="polyglot_book2_k", visible=False, ), ], [
                sg.Text("Opponent Search Info", font=("Segoe UI", 10), size=(30, 1),
                        right_click_menu=["Right", ["Show::right_search_info_k", "Hide::right_search_info_k"], ],
                        visible=False, )], [
                sg.Text("", key="search_info_all_k", size=(55, 1), font=("Segoe UI", 10), relief="sunken",
                        visible=False, )], [sg.Button("Moved", size=(5, 1), key="_moved_", visible=False)], ]

        white_controls = [[sg.Text("Human", font=("Segoe UI", 12, "bold"), key="_White_", size=(24, 1), ), sg.Push(),
                           sg.Text("", font=("Segoe UI", 12), key="w_base_time_k", size=(11, 1), relief='sunken'),
                           sg.Text("", font=("Segoe UI", 12), key="w_elapse_k", size=(11, 1), relief='sunken'), ]]

        black_controls = [[sg.Text("Computer", font=("Segoe UI", 12, "bold"), key="_Black_", size=(24, 1), ), sg.Push(),
                           sg.Text("", font=("Segoe UI", 12), key="b_base_time_k", size=(11, 1), relief='sunken'),
                           sg.Text("", font=("Segoe UI", 12), key="b_elapse_k", size=(11, 1), relief='sunken'), ]]

        board_tab = [[sg.Column(board_layout)]]

        self.menu_elem = sg.Menu(menu_def_neutral, tearoff=False)

        # White board layout, mode: Neutral
        other_column_layout = [[sg.Text("Move list", size=(None, 1), font=("Segoe UI", 10), expand_x=True)], [
            sg.Multiline("", do_not_clear=True, autoscroll=True, size=(52, 30), font=("Segoe UI", 10), key="_movelist_",
                         rstrip=False, disabled=True, )], ]

        column_layout = [[self.menu_elem], [sg.Column(black_controls, expand_x=True)], [sg.Column(board_tab)],
                         [sg.Column(white_controls, expand_x=True)], [sg.Column(board_controls)], ]

        layout = [[sg.Column(column_layout), sg.VSeperator(), sg.Column(other_column_layout)]]

        return layout

    def main_loop(self):
        """
        Build GUI, read user and engine config files and take user inputs.

        :return:
        """
        layout = self.build_main_layout(True)

        # Use white layout as default window
        window = sg.Window("{} {}".format(APP_NAME, APP_VERSION), layout, default_button_element_size=(12, 1),
                           auto_size_buttons=False)

        self.init_game()

        # Initialize White and black boxes
        while True:
            button, value = window.Read(timeout=50)
            self.update_labels_and_game_tags(window, human=self.username)
            break

        # Mode: Neutral, main loop starts here
        while True:
            button, value = window.Read(timeout=50)

            # Mode: Neutral
            if button is None:
                logging.info("Quit app from main loop, X is pressed.")
                break

            # Mode: Neutral, Set User time control
            if button == "User::tc_k":
                win_title = "Time/User"
                layout = [[sg.T("Base time (minute)", size=(16, 1)),
                           sg.Input(self.human_base_time_ms / 60 / 1000, key="base_time_k", size=(8, 1), ), ],
                          [sg.T("Increment (second)", size=(16, 1)),
                           sg.Input(self.human_inc_time_ms / 1000, key="inc_time_k", size=(8, 1)), ],
                          [sg.T("Period moves", size=(16, 1), visible=False),
                           sg.Input(self.human_period_moves, key="period_moves_k", size=(8, 1), visible=False, ), ], [
                              sg.Radio("Fischer", "tc_radio", key="fischer_type_k",
                                       default=True if self.human_tc_type == "fischer" else False, ),
                              sg.Radio("Delay", "tc_radio", key="delay_type_k",
                                       default=True if self.human_tc_type == "delay" else False, ), ],
                          [sg.OK(), sg.Cancel()], ]

                window.Hide()
                w = sg.Window(win_title, layout)
                while True:
                    e, v = w.Read(timeout=10)
                    if e is None:
                        break
                    if e == "Cancel":
                        break
                    if e == "OK":
                        base_time_ms = int(1000 * 60 * float(v["base_time_k"]))
                        inc_time_ms = int(1000 * float(v["inc_time_k"]))
                        period_moves = int(v["period_moves_k"])

                        tc_type = "fischer"
                        if v["fischer_type_k"]:
                            tc_type = "fischer"
                        elif v["delay_type_k"]:
                            tc_type = "delay"

                        self.human_base_time_ms = base_time_ms
                        self.human_inc_time_ms = inc_time_ms
                        self.human_period_moves = period_moves
                        self.human_tc_type = tc_type
                        break
                w.Close()
                window.UnHide()
                continue

            # Mode: Neutral, set username
            if button == "Set Name::user_name_k":
                win_title = "User/username"
                layout = [[sg.Text("Current username: {}".format(self.username))],
                          [sg.T("Name", size=(4, 1)), sg.Input(self.username, key="username_k", size=(32, 1)), ],
                          [sg.OK(), sg.Cancel()], ]
                window.Hide()
                w = sg.Window(win_title, layout)
                while True:
                    e, v = w.Read(timeout=10)
                    if e is None:
                        break
                    if e == "Cancel":
                        break
                    if e == "OK":
                        backup = self.username
                        username = self.username = v["username_k"]
                        if username == "":
                            username = backup
                        break
                w.Close()
                window.UnHide()
                self.update_labels_and_game_tags(window, human=self.username)
                continue

            # Mode: Neutral, Change theme
            if button in GUI_THEME:
                self.gui_theme = button
                window = self.create_new_window(window)
                continue

            # Mode: Neutral, Change board to gray
            if button == "Gray::board_color_k":
                self.sq_light_color = "#D8D8D8"
                self.sq_dark_color = "#808080"
                self.move_sq_light_color = "#e0e0ad"
                self.move_sq_dark_color = "#999966"
                self.redraw_board(window)
                window = self.create_new_window(window)
                continue

            # Mode: Neutral, Change board to green
            if button == "Green::board_color_k":
                self.sq_light_color = "#daf1e3"
                self.sq_dark_color = "#3a7859"
                self.move_sq_light_color = "#bae58f"
                self.move_sq_dark_color = "#6fbc55"
                self.redraw_board(window)
                window = self.create_new_window(window)
                continue

            # Mode: Neutral, Change board to blue
            if button == "Blue::board_color_k":
                self.sq_light_color = "#b9d6e8"
                self.sq_dark_color = "#4790c0"
                self.move_sq_light_color = "#d2e4ba"
                self.move_sq_dark_color = "#91bc9c"
                self.redraw_board(window)
                window = self.create_new_window(window)
                continue

            # Mode: Neutral, Change board to brown, default
            if button == "Brown::board_color_k":
                self.sq_light_color = "#F0D9B5"
                self.sq_dark_color = "#B58863"
                self.move_sq_light_color = "#E8E18E"
                self.move_sq_dark_color = "#B8AF4E"
                self.redraw_board(window)
                window = self.create_new_window(window)
                continue

            # Mode: Neutral
            if button == "Flip":
                window.find_element("_gamestatus_").update("Mode     Neutral")
                self.clear_elements(window)
                window = self.create_new_window(window, True)
                continue

            if button == 'Open Camera':
                layout = [[sg.Image(filename='', key='image')]]
                window_camera = sg.Window('Camera Viewfinder', layout, size=(640, 480))
                cap = cv2.VideoCapture(0)
                while True:
                    event_camera, values_camera = window_camera.read(timeout=1)
                    if event_camera == sg.WINDOW_CLOSED:
                        break
                    ret, frame = cap.read()
                    imgbytes = cv2.imencode('.png', frame)[1].tobytes()
                    window_camera['image'].update(data=imgbytes)
                window_camera.close()
                cap.release()

            # Mode: Neutral
            if button == "Play":
                # Change menu from Neutral to Play
                try:
                    sg.PopupOK("Calibrating camera, please put above an empty chessboard and don't move it "
                               "afterwards.", title=BOX_TITLE)

                    self.bella = MoveDetector()

                    sg.PopupOK("Camera calibrated. Please setup the board.", title=BOX_TITLE)

                    self.menu_elem.update(menu_def_play)
                    self.psg_board = copy.deepcopy(initial_board)
                    board = chess.Board()

                    self.bella.takePicture()

                    while True:
                        button, value = window.Read(timeout=100)

                        window.find_element("_gamestatus_").update("Mode     Play")
                        window.find_element("_movelist_").update(disabled=False)
                        window.find_element("_movelist_").update("", disabled=True)
                        window.find_element("_moved_").update(visible=True)

                        quit = self.play_game(window, board)
                        if quit:
                            break
                        window.find_element("_gamestatus_").update("Mode     Neutral")
                except ValueError:
                    sg.Popup("Invalid move.", title=BOX_TITLE)
                except Exception:
                    sg.Popup("Chessboard not found.", title=BOX_TITLE)

        window.Close()


def save_to_json_file(file, data):
    with open(file, "w") as json_file:
        json.dump(data, json_file, indent=4)


def main():
    theme = "Dark"
    pecg = EasyChessGui(theme)
    pecg.main_loop()


if __name__ == "__main__":
    main()
