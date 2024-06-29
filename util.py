import logging
import os
import platform as sys_plat
import sys
import cv2 as cv
import scipy.signal

log_format = "%(asctime)s :: %(funcName)s :: line: %(lineno)d :: %(levelname)s :: %(message)s"
logging.basicConfig(filename="pecg_log.txt", filemode="w", level=logging.DEBUG, format=log_format)

APP_NAME = "ELEC3442 Chess"
APP_VERSION = "v1.0.0_beta6.9"
BOX_TITLE = f"{APP_NAME} {APP_VERSION}"

platform = sys.platform
sys_os = sys_plat.system()

GUI_THEME = ["Dark", "Black", "Reddit"]

IMAGE_PATH = "Images/60"  # path to the chess pieces

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
                 [ROOKW, KNIGHTW, BISHOPW, QUEENW, KINGW, BISHOPW, KNIGHTW, ROOKW], ]

eval_list = []
best_move_white = []
best_move_black = []
wdl_white = []
wdl_black = []

evaluation_dictionary = []

"""
evaluation = [
    id: (black or white),
    move: best move,
    wdl: win, draw, loss,
    mate: mate in n,
    score: evaluation score,
]
"""

# Images/60
blank = os.path.join(IMAGE_PATH, "blank.png")
bishopB = os.path.join(IMAGE_PATH, "bB.png")
bishopW = os.path.join(IMAGE_PATH, "wB.png")
pawnB = os.path.join(IMAGE_PATH, "bP.png")
pawnW = os.path.join(IMAGE_PATH, "wP.png")
knightB = os.path.join(IMAGE_PATH, "bN.png")
knightW = os.path.join(IMAGE_PATH, "wN.png")
rookB = os.path.join(IMAGE_PATH, "bR.png")
rookW = os.path.join(IMAGE_PATH, "wR.png")
queenB = os.path.join(IMAGE_PATH, "bQ.png")
queenW = os.path.join(IMAGE_PATH, "wQ.png")
kingB = os.path.join(IMAGE_PATH, "bK.png")
kingW = os.path.join(IMAGE_PATH, "wK.png")

images = {BISHOPB: bishopB, BISHOPW: bishopW, PAWNB: pawnB, PAWNW: pawnW, KNIGHTB: knightB, KNIGHTW: knightW,
          ROOKB: rookB, ROOKW: rookW, KINGB: kingB, KINGW: kingW, QUEENB: queenB, QUEENW: queenW, BLANK: blank, }

# (1) Mode: Neutral
menu_def_neutral = [["&Mode", ["Play"]], ["Boar&d", ["Flip", "Color", ["Brown::board_color_k", "Blue::board_color_k",
                                                                       "Green::board_color_k", "Gray::board_color_k", ],
                                                     "Theme", GUI_THEME, ], ], ["&Time", ["User::tc_k"]],
                    ["&User", ["Set Name::user_name_k"]], ['&Camera', ['Open Camera']]]

# (2) Mode: Play, info: hide
menu_def_play = [["&Mode", ["Neutral"]]]

class BinaryConverter():
    def topkindex(self, arr, k):
        temp = []
        n = len(arr)
        if(n >= k):
            for i in range(n):
                temp.append((arr[i], i))
            temp = sorted(temp, reverse=True)[:k]
            return [x[1] for x in temp]
        return temp
    
    def convert(self,img_path):
        img = cv.imread(img_path, cv.IMREAD_GRAYSCALE)

        #Get buckets
        bucket = [0 for _ in range(255+1)]
        # for i in range(255+1):
        #     bucket.append(0)

        row, col = img.shape
        for i in range(row):
            for j in range(col):
                bucket[img[i][j]]+=1

        #Get Treshold
        yhat = scipy.signal.savgol_filter(bucket, 100, 3) # Approximating: window size 51, polynomial order 3
        peaks = scipy.signal.find_peaks(yhat)[0] #Returns x values

        #Getting the actual values of the peaks
        peak_y = []
        for p in peaks:
            peak_y.append(yhat[p]) 

        #Getting the bounds for the through
        indices = self.topkindex(peak_y, 2) #Find top 2 peaks
        bounds = [x for index, x in enumerate(peaks) if index in indices]

        lower_bound, upper_bound = min(bounds), max(bounds)

        #Find pixel with the lowest value
        treshold = (lower_bound, yhat[lower_bound])
        for i in range(lower_bound, upper_bound):
            val = yhat[i]
            if val<treshold[1]:
                treshold=(i, val)

        #Apply treshold (Inverted in this case)
        row, col = img.shape
        for i in range(row):
            for j in range(col):
                if img[i][j]<treshold[0]:
                    img[i][j] = 1
                else:
                    img[i][j] = 0
        
        return img
