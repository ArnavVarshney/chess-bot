import logging
import os
import sys

import chess.polyglot

log_format = '%(asctime)s :: %(funcName)s :: line: %(lineno)d :: %(levelname)s :: %(message)s'
logging.basicConfig(filename='pecg_log.txt', filemode='w', level=logging.DEBUG, format=log_format)

APP_NAME = 'ELEC3442 - Chess Robot'
APP_VERSION = 'v1.2'
BOX_TITLE = f'{APP_NAME} {APP_VERSION}'

platform = sys.platform
sys_os = 'linux' if platform.startswith('linux') else 'darwin' if platform.startswith('darwin') else 'win32'

ico_path = {'win32': {'pecg': 'Icon/pecg.ico', 'enemy': 'Icon/enemy.ico'},
            'linux': {'pecg': 'Icon/pecg.png', 'enemy': 'Icon/enemy.png'},
            'darwin': {'pecg': 'Icon/pecg.png', 'enemy': 'Icon/enemy.png'}}

MIN_DEPTH = 1
MAX_DEPTH = 1000
GUI_THEME = ['Dark', 'Reddit', 'Black']

IMAGE_PATH = 'Images/60'  # path to the chess pieces

BLANK = 0  # piece names
PAWNB = 1
KNIGHTB = 2
BISHOPB = 3
ROOKB = 4
KINGB = 5
QUEENB = 6
PAWNW = 7
KNIGHTW = 8
BISHOPW = 9
ROOKW = 10
KINGW = 11
QUEENW = 12

# Absolute rank based on real chess board, white at bottom, black at the top.
# This is also the rank mapping used by python-chess modules.
RANK_8 = 7
RANK_7 = 6
RANK_6 = 5
RANK_5 = 4
RANK_4 = 3
RANK_3 = 2
RANK_2 = 1
RANK_1 = 0

initial_board = [[ROOKB, KNIGHTB, BISHOPB, QUEENB, KINGB, BISHOPB, KNIGHTB, ROOKB], [PAWNB, ] * 8, [BLANK, ] * 8,
                 [BLANK, ] * 8, [BLANK, ] * 8, [BLANK, ] * 8, [PAWNW, ] * 8,
                 [ROOKW, KNIGHTW, BISHOPW, QUEENW, KINGW, BISHOPW, KNIGHTW, ROOKW]]

white_init_promote_board = [[QUEENW, ROOKW, BISHOPW, KNIGHTW]]

black_init_promote_board = [[QUEENB, ROOKB, BISHOPB, KNIGHTB]]

HELP_MSG = """The GUI has 2 modes, Play and Neutral. After startup
you are in Neutral mode. You can go to mode Play through Mode menu.

All games are auto-saved in pecg_auto_save_games.pgn.
Visit Game menu in Play mode to see other options to save the game.

It has to be noted you need to setup an engine to make the GUI works.
You can view which engines are ready for use via:
Engine->Set Engine Opponent.

(A) To setup an engine, you should be in Neutral mode.
1. Engine->Manage->Install, press the add button.
2. After engine setup, you can configure the engine options with:
  a. Engine->Manage-Edit
  b. Select the engine you want to edit and press Modify.

Before playing a game, you should select an engine opponent via
Engine->Set Engine Opponent.

You can also set an engine Adviser in the Engine menu.
During a game you can ask help from Adviser by right-clicking
the Adviser label and press show.

(B) To play a game
You should be in Play mode.
1. Mode->Play
2. Make move on the board

(C) To play as black
You should be in Neutral mode
1. Board->Flip
2. Mode->Play
3. Engine->Go
If you are already in Play mode, go back to
Neutral mode via Mode->Neutral

(D) To flip board
You should be in Neutral mode
1. Board->Flip

(E) To paste FEN
You should be in Play mode
1. Mode->Play
2. FEN->Paste

(F) To show engine search info after the move
1. Right-click on the Opponent Search Info and press Show

(G) To Show book 1 and 2
1. Right-click on Book 1 or 2 press Show

(H) To change board color
1. You should be in Neutral mode.
2. Board->Color.

(I) To change board theme
1. You should be in Neutral mode.
2. Board->Theme.
"""

# Images/60
blank = os.path.join(IMAGE_PATH, 'blank.png')
bishopB = os.path.join(IMAGE_PATH, 'bB.png')
bishopW = os.path.join(IMAGE_PATH, 'wB.png')
pawnB = os.path.join(IMAGE_PATH, 'bP.png')
pawnW = os.path.join(IMAGE_PATH, 'wP.png')
knightB = os.path.join(IMAGE_PATH, 'bN.png')
knightW = os.path.join(IMAGE_PATH, 'wN.png')
rookB = os.path.join(IMAGE_PATH, 'bR.png')
rookW = os.path.join(IMAGE_PATH, 'wR.png')
queenB = os.path.join(IMAGE_PATH, 'bQ.png')
queenW = os.path.join(IMAGE_PATH, 'wQ.png')
kingB = os.path.join(IMAGE_PATH, 'bK.png')
kingW = os.path.join(IMAGE_PATH, 'wK.png')

images = {BISHOPB: bishopB, BISHOPW: bishopW, PAWNB: pawnB, PAWNW: pawnW, KNIGHTB: knightB, KNIGHTW: knightW,
          ROOKB: rookB, ROOKW: rookW, KINGB: kingB, KINGW: kingW, QUEENB: queenB, QUEENW: queenW, BLANK: blank}

# Promote piece from psg (pysimplegui) to pyc (python-chess)
promote_psg_to_pyc = {KNIGHTB: chess.KNIGHT, BISHOPB: chess.BISHOP, ROOKB: chess.ROOK, QUEENB: chess.QUEEN,
                      KNIGHTW: chess.KNIGHT, BISHOPW: chess.BISHOP, ROOKW: chess.ROOK, QUEENW: chess.QUEEN}

INIT_PGN_TAG = {'Event': 'Human vs Robot', 'White': 'Human', 'Black': 'Computer'}

# (1) Mode: Neutral
menu_def_neutral = [['&Mode', ['Play']], ['Boar&d', ['Flip', 'Color', ['Brown::board_color_k', 'Blue::board_color_k',
                                                                       'Green::board_color_k', 'Gray::board_color_k'],
                                                     'Theme', GUI_THEME]],
                    ['&Engine', ['Set Engine ELO']],
                    ['&Time', ['User::tc_k', 'Engine::tc_k']],
                    ['&User', ['Set Name::user_name_k']],
                    ['&Camera', ['Open Camera']],
                    ['&Help', ['GUI']], ]

# (2) Mode: Play, info: hide
menu_def_play = [['&Mode', ['Neutral']], ['&Game', ['&New::new_game_k',  # 'Save to My Games::save_game_k',
                                                    # 'Save to White Repertoire',
                                                    # 'Save to Black Repertoire',
                                                    # 'Resign::resign_game_k',
                                                    # 'User Wins::user_wins_k',
                                                    # 'User Draws::user_draws_k'
                                                    ]],  # ['FEN', ['Paste']],
                 # ['&Engine', ['Go', 'Move Now']],
                 ['&Help', ['GUI']], ]
