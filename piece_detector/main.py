# CPU vs CPU
from board import *


def main():
    cpu1 = Board(bypass="dummy_input/empty1.jpg", id=1)
    cpu2 = Board(bypass="dummy_input/empty1.jpg", id=2)

    #Set up initial ground truth
    pos={'A1': ['black_queen'], 'A2': ['empty'], 'A3': ['empty'], 'A4': ['empty'], 'A5': ['empty'], 'A6': ['empty'], 'A7': ['empty'], 'A8': ['empty'], 
        'B1': ['empty'], 'B2': ['empty'], 'B3': ['empty'], 'B4': ['empty'], 'B5': ['empty'], 'B6': ['empty'], 'B7': ['empty'], 'B8': ['empty'], 
        'C1': ['empty'], 'C2': ['empty'], 'C3': ['empty'], 'C4': ['empty'], 'C5': ['empty'], 'C6': ['empty'], 'C7': ['empty'], 'C8': ['empty'], 
        'D1': ['empty'], 'D2': ['empty'], 'D3': ['empty'], 'D4': ['empty'], 'D5': ['empty'], 'D6': ['empty'], 'D7': ['empty'], 'D8': ['empty'], 
        'E1': ['empty'], 'E2': ['empty'], 'E3': ['empty'], 'E4': ['black_king'], 'E5': ['empty'], 'E6': ['empty'], 'E7': ['empty'], 'E8': ['empty'], 
        'F1': ['empty'], 'F2': ['empty'], 'F3': ['empty'], 'F4': ['empty'], 'F5': ['empty'], 'F6': ['empty'], 'F7': ['empty'], 'F8': ['empty'], 
        'G1': ['empty'], 'G2': ['black_pawn'], 'G3': ['empty'], 'G4': ['empty'], 'G5': ['empty'], 'G6': ['empty'], 'G7': ['empty'], 'G8': ['empty'], 
        'H1': ['empty'], 'H2': ['empty'], 'H3': ['empty'], 'H4': ['empty'], 'H5': ['empty'], 'H6': ['empty'], 'H7': ['empty'], 'H8': ['empty']}
    cpu1.setPos(pos)
    cpu2.setPos(pos)
    draw_board(pos)

    images = ["dummy_input/filled1.jpg","dummy_input/filled2.jpg"] #temporary

    turn = 0
    players = [cpu1, cpu2]
    while players[turn].make_move(): #While a player can still make a move; Main game loop
        #visualization
        draw_board(players[turn].pos)

        #scans board
        img = cv.imread(images.pop(0))
        players[(turn+1)%2].getPiecesPosition(img)

        # Check if matching ground truth
        if not players[(turn+1)%2].valid(players[turn].pos):
            print("Fixing...")
            players[(turn+1)%2].setPos(players[turn].pos)
        
        #End turn
        turn = (turn+1)%2

    print("\n\nGame over")
    return

def draw_board(pos):
    print("\n\n")
    keys = list(pos.keys())

    i=0
    while i <  len(keys):
        print(keys[i][0])

        for _ in range(8):
            print(pos[keys[i]], end="\t")
            i+=1
        print("")
    print("\n\n")
    return

if __name__ == "__main__":
    main()