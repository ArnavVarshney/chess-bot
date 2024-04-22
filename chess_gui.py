"""
PySimpleGUI Square Mapping
board = [
    56, 57, ... 63
    ...
    8, 9, ...
    0, 1, 2, ...
]

row = [
    0, 0, ...
    1, 1, ...
    ...
    7, 7 ...
]

col = [
    0, 1, 2, ... 7
    0, 1, 2, ...
    ...
    0, 1, 2, ... 7
]


Python-Chess Square Mapping
board is the same as in PySimpleGUI
row is reversed
col is the same as in PySimpleGUI

"""

import copy
import queue
from datetime import datetime

import PySimpleGUI as pSG
import cv2

from classes import *
from util import *


class EasyChessGui:
    queue = queue.Queue()
    is_user_white = True  # White is at the bottom in board layout

    def __init__(self, theme):
        self.node = None
        self.theme = theme
        self.init_game()
        self.fen = None
        self.psg_board = None
        self.menu_elem = None
        self.username = 'Human'

        self.human_base_time_ms = 5 * 60 * 1000  # 5 minutes
        self.human_inc_time_ms = 10 * 1000  # 10 seconds
        self.human_period_moves = 0
        self.human_tc_type = 'fischer'

        self.engine_base_time_ms = 3 * 60 * 1000  # 5 minutes
        self.engine_inc_time_ms = 2 * 1000  # 10 seconds
        self.engine_period_moves = 0
        self.engine_tc_type = 'fischer'

        # Default board color is brown
        self.sq_light_color = '#F0D9B5'
        self.sq_dark_color = '#B58863'

        # Move highlight, for brown board
        self.move_sq_light_color = '#E8E18E'
        self.move_sq_dark_color = '#B8AF4E'

        self.gui_theme = theme

    def create_new_window(self, window, flip=False):
        """Hide current window and creates a new window."""
        loc = window.CurrentLocation()
        window.Hide()
        if flip:
            self.is_user_white = not self.is_user_white

        layout = self.build_main_layout(self.is_user_white)

        w = pSG.Window('{} {}'.format(APP_NAME, APP_VERSION), layout, default_button_element_size=(12, 1),
                       auto_size_buttons=False, location=(loc[0], loc[1]), icon=ico_path[platform]['pecg'])

        # Initialize White and black boxes
        while True:
            button, value = w.Read(timeout=50)
            self.update_labels_and_game_tags(w, human=self.username)
            break

        window.Close()
        return w

    def get_time_mm_ss_ms(self, time_ms):
        """ Returns time in min:sec:millisec given time in millisec """
        s, ms = divmod(int(time_ms), 1000)
        m, s = divmod(s, 60)

        return '{:02d}m:{:02d}s'.format(m, s)

    def get_time_h_mm_ss(self, time_ms, symbol=True):
        """
        Returns time in h:mm:ss format.

        :param time_ms:
        :param symbol:
        :return:
        """
        s, ms = divmod(int(time_ms), 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)

        if not symbol:
            return '{:01d}:{:02d}:{:02d}'.format(h, m, s)
        return '{:01d}h:{:02d}m:{:02d}s'.format(h, m, s)

    def get_tag_date(self):
        """ Return date in pgn tag date format """
        return datetime.today().strftime('%Y.%m.%d')

    def init_game(self):
        """ Initialize game with initial pgn tag values """
        self.game = chess.pgn.Game()
        self.node = None
        self.game.headers['Event'] = INIT_PGN_TAG['Event']
        self.game.headers['Date'] = self.get_tag_date()
        self.game.headers['White'] = INIT_PGN_TAG['White']
        self.game.headers['Black'] = INIT_PGN_TAG['Black']

    def set_new_game(self):
        """ Initialize new game but save old pgn tag values"""
        # Define a game object for saving game in pgn format
        self.game = chess.pgn.Game()

    def clear_elements(self, window):
        """ Clear movelist, score, pv, time, depth and nps boxes """
        window.find_element('_movelist_').update(disabled=False)
        window.find_element('_movelist_').update('', disabled=True)
        window.Element('w_base_time_k').update('')
        window.Element('b_base_time_k').update('')
        window.Element('w_elapse_k').update('')
        window.Element('b_elapse_k').update('')

    def update_labels_and_game_tags(self, window, human='Human'):
        """ Update player names """
        engine_id = 'Robot'
        if self.is_user_white:
            window.find_element('_White_').update(human)
            window.find_element('_Black_').update(engine_id)
            self.game.headers['White'] = human
            self.game.headers['Black'] = engine_id
        else:
            window.find_element('_White_').update(engine_id)
            window.find_element('_Black_').update(human)
            self.game.headers['White'] = engine_id
            self.game.headers['Black'] = human

    def change_square_color(self, window, row, col):
        """
        Change the color of a square based on square row and col.
        """
        btn_sq = window.find_element(key=(row, col))
        is_dark_square = True if (row + col) % 2 else False
        bd_sq_color = self.move_sq_dark_color if is_dark_square else self.move_sq_light_color
        btn_sq.update(button_color=('white', bd_sq_color))

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
        In contrast, Python-chess square mapping is 0 at the bottom and 7
        at the top. chess.square_rank() is a method from Python-chess that
        returns row given square s.

        :param s: square
        :return: row
        """
        return 7 - chess.square_rank(s)

    def get_col(self, s):
        """ Returns col given square s """
        return chess.square_file(s)

    def redraw_board(self, window):
        """
        Redraw board at start and after a move.

        :param window:
        :return:
        """
        for i in range(8):
            for j in range(8):
                color = self.sq_dark_color if (i + j) % 2 else self.sq_light_color
                piece_image = images[self.psg_board[i][j]]
                elem = window.find_element(key=(i, j))
                elem.update(button_color=('white', color), image_filename=piece_image, )

    def render_square(self, image, key, location):
        """ Returns an RButton (Read Button) with image """
        if (location[0] + location[1]) % 2:
            color = self.sq_dark_color  # Dark square
        else:
            color = self.sq_light_color
        return pSG.RButton('', image_filename=image, size=(1, 1), border_width=0, button_color=('white', color),
                           pad=(0, 0), key=key)

    def define_timer(self, window, name='human'):
        """
        Returns Timer object for either human or engine.
        """
        if name == 'human':
            timer = Timer(self.human_tc_type, self.human_base_time_ms, self.human_inc_time_ms, self.human_period_moves)
        else:
            timer = Timer(self.engine_tc_type, self.engine_base_time_ms, self.engine_inc_time_ms,
                          self.engine_period_moves)

        elapse_str = self.get_time_h_mm_ss(timer.base)
        is_white_base = (self.is_user_white and name == 'human') or (not self.is_user_white and name != 'human')
        window.Element('w_base_time_k' if is_white_base else 'b_base_time_k').update(elapse_str)

        return timer

    def play_game(self, window: pSG.Window, board: chess.Board):
        """Play a game against an engine or human.

        Args:
          window: A PySimplegUI window.
          board: current board position
        """
        window.find_element('_movelist_').update(disabled=False)
        window.find_element('_movelist_').update('', disabled=True)

        is_human_stm = True if self.is_user_white else False

        is_new_game, is_exit_game, is_exit_app = False, False, False

        # Do not play immediately when stm is computer
        is_engine_ready = True if is_human_stm else False

        # For saving game
        move_cnt = 0

        is_user_resigns = False
        is_user_wins = False
        is_user_draws = False

        # Init timer
        human_timer = self.define_timer(window)
        engine_timer = self.define_timer(window, 'engine')

        # Game loop
        while not board.is_game_over(claim_draw=True):

            # Mode: Play, Stm: computer (first move), Allow user to change settings.
            # User can start the engine by Engine->Go.

            # If side to move is human
            if is_human_stm:
                window.find_element('move_completed').update(visible=True)
                while True:
                    button, value = window.Read(timeout=100)

                    # Update elapse box in m:s format
                    elapse_str = self.get_time_mm_ss_ms(human_timer.elapse)
                    k = 'w_elapse_k'
                    if not self.is_user_white:
                        k = 'b_elapse_k'
                    window.Element(k).update(elapse_str)
                    human_timer.elapse += 100

                    if button is None:
                        logging.info('Quit app X is pressed.')
                        is_exit_app = True
                        break

                    # Mode: Play, Stm: User
                    if button == 'New::new_game_k':
                        is_new_game = True
                        self.clear_elements(window)
                        break

                    # Mode: Play, stm: User
                    if button == 'Resign::resign_game_k':
                        logging.info('User resigns')

                        # Verify resign
                        reply = pSG.Popup('Do you really want to resign?', button_type=pSG.POPUP_BUTTONS_YES_NO,
                                          title=BOX_TITLE, icon=ico_path[platform]['pecg'])
                        if reply == 'Yes':
                            is_user_resigns = True
                            break
                        else:
                            continue

                    # Mode: Play, stm: User
                    if button == 'User Wins::user_wins_k':
                        logging.info('User wins by adjudication')
                        is_user_wins = True
                        break

                    # Mode: Play, stm: User
                    if button == 'User Draws::user_draws_k':
                        logging.info('User draws by adjudication')
                        is_user_draws = True
                        break

                    # Mode: Play, Stm: User
                    if button == 'Neutral':
                        reply = pSG.Popup('Do you really want to exit?', button_type=pSG.POPUP_BUTTONS_YES_NO,
                                          title=BOX_TITLE, icon=ico_path[platform]['pecg'])
                        if reply == 'Yes':
                            is_exit_game = True
                            self.clear_elements(window)
                            break
                        else:
                            continue

                    # Mode: Play, stm: User
                    if button == 'GUI':
                        pSG.PopupScrolled(HELP_MSG, title=BOX_TITLE, )
                        break

                    # Mode: Play, stm: User
                    if button == 'move_completed':
                        is_human_stm = False
                        break

            # Else if side to move is not human
            else:
                window.find_element('_gamestatus_').update(MODE_PLAY + '. Engine is thinking...')
                window.find_element('move_completed').update(visible=False)
                while True:
                    button, value = window.Read(timeout=100)

                    # Mode: Play, Stm: computer (first move)
                    if button == 'New::new_game_k':
                        is_new_game = True
                        break

                    # Mode: Play, Stm: Computer first move
                    if button == 'Neutral':
                        is_exit_game = True
                        break

                    if button == 'GUI':
                        pSG.PopupScrolled(HELP_MSG, title=BOX_TITLE)
                        continue

                    if button is None:
                        logging.info('Quit app X is pressed.')
                        is_exit_app = True
                        break

                is_promote = False
                best_move = None

                # Mode: Play, stm: Computer, If there is no book move,
                # let the engine search the best move
                # TODO: Add stockfish

                # If engine failed to send a legal move
                if best_move is None:
                    break

                # Update board with computer move
                move_str = str(best_move)
                fr_col = ord(move_str[0]) - ord('a')
                fr_row = 8 - int(move_str[1])
                to_col = ord(move_str[2]) - ord('a')
                to_row = 8 - int(move_str[3])

                piece = self.psg_board[fr_row][fr_col]
                self.psg_board[fr_row][fr_col] = BLANK

                self.redraw_board(window)

                board.push(best_move)
                move_cnt += 1

                # Update timer
                engine_timer.update_base()

                # Update game, move from engine
                time_left = engine_timer.base

                self.update_game(move_cnt, best_move, time_left)

                window.find_element('_movelist_').update(disabled=False)
                window.find_element('_movelist_').update('')
                window.find_element('_movelist_').update(self.game.variations[0], append=True, disabled=True)

                # Change the color of the "fr" and "to" board squares
                self.change_square_color(window, fr_row, fr_col)
                self.change_square_color(window, to_row, to_col)

                is_human_stm = not is_human_stm
                # Engine has done its move

                k1 = 'b_elapse_k'
                k2 = 'b_base_time_k'
                if not self.is_user_white:
                    k1 = 'w_elapse_k'
                    k2 = 'w_base_time_k'

                # Update elapse box
                elapse_str = self.get_time_mm_ss_ms(engine_timer.elapse)
                window.Element(k1).update(elapse_str)

                # Update remaining time box
                elapse_str = self.get_time_h_mm_ss(engine_timer.base)
                window.Element(k2).update(elapse_str)

                window.find_element('_gamestatus_').update(MODE_PLAY)

            if is_new_game or is_exit_game or is_exit_app or is_user_resigns or is_user_wins or is_user_draws:
                break

        # Auto-save game
        logging.info('Saving game automatically')
        if is_user_resigns:
            self.game.headers['Result'] = '0-1' if self.is_user_white else '1-0'
            self.game.headers['Termination'] = '{} resigns'.format('white' if self.is_user_white else 'black')
        elif is_user_wins:
            self.game.headers['Result'] = '1-0' if self.is_user_white else '0-1'
            self.game.headers['Termination'] = 'Adjudication'
        elif is_user_draws:
            self.game.headers['Result'] = '1/2-1/2'
            self.game.headers['Termination'] = 'Adjudication'
        else:
            self.game.headers['Result'] = board.result(claim_draw=True)

        base_h = int(self.human_base_time_ms / 1000)
        inc_h = int(self.human_inc_time_ms / 1000)
        base_e = int(self.engine_base_time_ms / 1000)
        inc_e = int(self.engine_inc_time_ms / 1000)

        if self.is_user_white:
            if self.human_tc_type == 'fischer':
                self.game.headers['WhiteTimeControl'] = str(base_h) + '+' + str(inc_h)
            elif self.human_tc_type == 'delay':
                self.game.headers['WhiteTimeControl'] = str(base_h) + '-' + str(inc_h)
            if self.engine_tc_type == 'fischer':
                self.game.headers['BlackTimeControl'] = str(base_e) + '+' + str(inc_e)
            elif self.engine_tc_type == 'timepermove':
                self.game.headers['BlackTimeControl'] = str(1) + '/' + str(base_e)
        else:
            if self.human_tc_type == 'fischer':
                self.game.headers['BlackTimeControl'] = str(base_h) + '+' + str(inc_h)
            elif self.human_tc_type == 'delay':
                self.game.headers['BlackTimeControl'] = str(base_h) + '-' + str(inc_h)
            if self.engine_tc_type == 'fischer':
                self.game.headers['WhiteTimeControl'] = str(base_e) + '+' + str(inc_e)
            elif self.engine_tc_type == 'timepermove':
                self.game.headers['WhiteTimeControl'] = str(1) + '/' + str(base_e)

        if board.is_game_over(claim_draw=True):
            pSG.Popup('Game is over.', title=BOX_TITLE, icon=ico_path[platform]['pecg'])

        if is_exit_app:
            window.Close()
            sys.exit(0)

        self.clear_elements(window)

        return False if is_exit_game else is_new_game

    def create_board(self, is_user_white=True):
        """
        Returns board layout based on color of user. If user is white,
        the white pieces will be at the bottom, otherwise at the top.

        :param is_user_white: user has handling the white pieces
        :return: board layout
        """
        self.psg_board = copy.deepcopy(initial_board)

        board_layout = []

        if is_user_white:
            # Save the board with black at the top.
            start = 0
            end = 8
            step = 1
        else:
            start = 7
            end = -1
            step = -1

        # Loop through the board and create buttons with images
        for i in range(start, end, step):
            # Row numbers at left of board is blank
            row = []
            for j in range(start, end, step):
                piece_image = images[self.psg_board[i][j]]
                row.append(self.render_square(piece_image, key=(i, j), location=(i, j)))
            board_layout.append(row)

        return board_layout

    def build_main_layout(self, is_user_white=True):
        """
        Creates all elements for the GUI, including the board layout.

        :param is_user_white: if user is white, the white pieces are
        oriented such that the white pieces are at the bottom.
        :return: GUI layout
        """
        pSG.ChangeLookAndFeel(self.gui_theme)
        pSG.SetOptions(margins=(0, 3), border_width=1)

        # Define board
        board_layout = self.create_board(is_user_white)

        board_controls = [
            [pSG.Text(MODE_NEUTRAL, size=(36, 1), font=('Consolas', 10), key='_gamestatus_')],
            [pSG.Text('White', size=(7, 1), font=('Consolas', 10)),
             pSG.Text('Human', font=('Consolas', 10), key='_White_', size=(24, 1), relief='sunken'),
             pSG.Text('', font=('Consolas', 10), key='w_base_time_k', size=(11, 1), relief='sunken'),
             pSG.Text('', font=('Consolas', 10), key='w_elapse_k', size=(7, 1), relief='sunken')],
            [pSG.Text('Black', size=(7, 1), font=('Consolas', 10)),
             pSG.Text('Computer', font=('Consolas', 10), key='_Black_', size=(24, 1), relief='sunken'),
             pSG.Text('', font=('Consolas', 10), key='b_base_time_k', size=(11, 1), relief='sunken'),
             pSG.Text('', font=('Consolas', 10), key='b_elapse_k', size=(7, 1), relief='sunken')],
            [pSG.Text('Move list', size=(16, 1), font=('Consolas', 10))], [
                pSG.Multiline('', do_not_clear=True, autoscroll=True, size=(52, 8), font=('Consolas', 10),
                              key='_movelist_', disabled=True)],
            [pSG.Button('Move Completed', key='move_completed', visible=False)]]

        board_tab = [[pSG.Column(board_layout)]]

        self.menu_elem = pSG.Menu(menu_def_neutral, tearoff=False)

        # White board layout, mode: Neutral
        layout = [[self.menu_elem], [pSG.Column(board_tab), pSG.Column(board_controls)]]

        return layout

    def main_loop(self):
        """
        Build GUI, read user and engine config files and take user inputs.

        :return:
        """
        layout = self.build_main_layout(True)

        # Use white layout as default window
        window = pSG.Window('{} {}'.format(APP_NAME, APP_VERSION), layout, default_button_element_size=(12, 1),
                            auto_size_buttons=False, icon=ico_path[platform]['pecg'], finalize=True)

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
                logging.info('Quit app from main loop, X is pressed.')
                break

            if button == 'Open Camera':
                layout = [[pSG.Image(filename='', key='image')]]
                window_camera = pSG.Window('Camera Viewfinder', layout, size=(640, 480))
                cap = cv2.VideoCapture(0)
                while True:
                    event_camera, values_camera = window_camera.read(timeout=1)
                    if event_camera == pSG.WINDOW_CLOSED:
                        break
                    ret, frame = cap.read()
                    imgbytes = cv2.imencode('.png', frame)[1].tobytes()
                    window_camera['image'].update(data=imgbytes)
                window_camera.close()
                cap.release()

            # Mode: Neutral, Set User time control
            if button == 'User::tc_k':
                win_title = 'Time/User'
                layout = [[pSG.T('Base time (minute)', size=(16, 1)),
                           pSG.Input(self.human_base_time_ms / 60 / 1000, key='base_time_k', size=(8, 1))],
                          [pSG.T('Increment (second)', size=(16, 1)),
                           pSG.Input(self.human_inc_time_ms / 1000, key='inc_time_k', size=(8, 1))],
                          [pSG.T('Period moves', size=(16, 1), visible=False),
                           pSG.Input(self.human_period_moves, key='period_moves_k', size=(8, 1), visible=False)], [
                              pSG.Radio('Fischer', 'tc_radio', key='fischer_type_k',
                                        default=True if self.human_tc_type == 'fischer' else False),
                              pSG.Radio('Delay', 'tc_radio', key='delay_type_k',
                                        default=True if self.human_tc_type == 'delay' else False)],
                          [pSG.OK(), pSG.Cancel()]]

                window.Hide()
                w = pSG.Window(win_title, layout, icon=ico_path[platform]['pecg'])
                while True:
                    e, v = w.Read(timeout=10)
                    if e is None:
                        break
                    if e == 'Cancel':
                        break
                    if e == 'OK':
                        base_time_ms = int(1000 * 60 * float(v['base_time_k']))
                        inc_time_ms = int(1000 * float(v['inc_time_k']))
                        period_moves = int(v['period_moves_k'])

                        tc_type = 'fischer'
                        if v['fischer_type_k']:
                            tc_type = 'fischer'
                        elif v['delay_type_k']:
                            tc_type = 'delay'

                        self.human_base_time_ms = base_time_ms
                        self.human_inc_time_ms = inc_time_ms
                        self.human_period_moves = period_moves
                        self.human_tc_type = tc_type
                        break
                w.Close()
                window.UnHide()
                continue

            # Mode: Neutral, Set engine time control
            if button == 'Engine::tc_k':
                win_title = 'Time/Engine'
                layout = [[pSG.T('Base time (minute)', size=(16, 1)),
                           pSG.Input(self.engine_base_time_ms / 60 / 1000, key='base_time_k', size=(8, 1))],
                          [pSG.T('Increment (second)', size=(16, 1)),
                           pSG.Input(self.engine_inc_time_ms / 1000, key='inc_time_k', size=(8, 1))],
                          [pSG.T('Period moves', size=(16, 1), visible=False),
                           pSG.Input(self.engine_period_moves, key='period_moves_k', size=(8, 1), visible=False)], [
                              pSG.Radio('Fischer', 'tc_radio', key='fischer_type_k',
                                        default=True if self.engine_tc_type == 'fischer' else False),
                              pSG.Radio('Time Per Move', 'tc_radio', key='timepermove_k',
                                        default=True if self.engine_tc_type == 'timepermove' else False,
                                        tooltip='Only base time will be used.')], [pSG.OK(), pSG.Cancel()]]

                window.Hide()
                w = pSG.Window(win_title, layout, icon=ico_path[platform]['pecg'])
                while True:
                    e, v = w.Read(timeout=10)
                    if e is None:
                        break
                    if e == 'Cancel':
                        break
                    if e == 'OK':
                        base_time_ms = int(1000 * 60 * float(v['base_time_k']))
                        inc_time_ms = int(1000 * float(v['inc_time_k']))
                        period_moves = int(v['period_moves_k'])

                        tc_type = 'fischer'
                        if v['fischer_type_k']:
                            tc_type = 'fischer'
                        elif v['timepermove_k']:
                            tc_type = 'timepermove'

                        self.engine_base_time_ms = base_time_ms
                        self.engine_inc_time_ms = inc_time_ms
                        self.engine_period_moves = period_moves
                        self.engine_tc_type = tc_type
                        break
                w.Close()
                window.UnHide()
                continue

            # Mode: Neutral, set username
            if button == 'Set Name::user_name_k':
                win_title = 'User/username'
                layout = [[pSG.Text('Current username: {}'.format(self.username))],
                          [pSG.T('Name', size=(4, 1)), pSG.Input(self.username, key='username_k', size=(32, 1))],
                          [pSG.OK(), pSG.Cancel()]]
                window.Hide()
                w = pSG.Window(win_title, layout, icon=ico_path[platform]['pecg'])
                while True:
                    e, v = w.Read(timeout=10)
                    if e is None:
                        break
                    if e == 'Cancel':
                        break
                    if e == 'OK':
                        backup = self.username
                        username = self.username = v['username_k']
                        if username == '':
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

            # Mode: Neutral
            if button == 'Flip':
                window.find_element('_gamestatus_').update(MODE_NEUTRAL)
                self.clear_elements(window)
                window = self.create_new_window(window, True)
                continue

            # Mode: Neutral
            if button == 'GUI':
                pSG.PopupScrolled(HELP_MSG, title='Help/GUI')
                continue

            # Mode: Neutral
            if button == 'Play':
                # Change menu from Neutral to Play
                self.menu_elem.update(menu_def_play)
                self.psg_board = copy.deepcopy(initial_board)
                board = chess.Board()

                while True:
                    button, value = window.Read(timeout=100)

                    window.find_element('_gamestatus_').update(MODE_PLAY)
                    window.find_element('_movelist_').update(disabled=False)
                    window.find_element('_movelist_').update('', disabled=True)

                    start_new_game = self.play_game(window, board)
                    window.find_element('_gamestatus_').update(MODE_NEUTRAL)

                    self.psg_board = copy.deepcopy(initial_board)
                    self.redraw_board(window)
                    board = chess.Board()
                    self.set_new_game()

                    if not start_new_game:
                        break

                # Restore Neutral menu
                self.menu_elem.update(menu_def_neutral)
                self.psg_board = copy.deepcopy(initial_board)
                self.set_new_game()
                continue

        window.Close()


def main():
    theme = 'Dark'
    pecg = EasyChessGui(theme)
    pecg.main_loop()


if __name__ == "__main__":
    main()
