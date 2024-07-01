import os
from time import sleep
import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
from util import *
import copy
from classifier import *

#k x k board
class Board:
    cap = None
    boxes = {}
    directory = "output/board"
    cropped_directory = "output/cropped"
    k = 7
    classifier = None
    # translation = {"A": "H", "H": "A", "B": "G", "G": "B", "C": "F", "F": "C", "D": "E", "E": "D"}

    def __init__(self, cam=0, bypass=None):
        print("---\n")
        # self.cap = cv.VideoCapture(cam)
        # self.cap.set(3, 1920)
        # self.cap.set(4, 1080)
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory)
        if not os.path.isdir(self.cropped_directory):
            os.makedirs(self.cropped_directory)
        self.boxes = self.calibrate(bypass)
        self.classifier = PieceClassifier()
        print("\n---")
        return
    
    def getPiecesPosition(self, image):
        pos={}
        for box in self.boxes:
            img = crop(image, self.boxes[box])

            #Visualization
            plt.imsave(self.cropped_directory+"/"+box+".jpg", cv.cvtColor(img,cv.COLOR_BGR2RGB))

            pos[box] = self.classifier.getLabelNames(self.classifier.predict([img]))
        return pos
    
    def sortChessBoardCorners(self, corners):
        k = self.k
        sorted_points = []

        #Find point furthest from origin
        top = -1
        pos = -1
        for index, point in enumerate(corners):
            x,y = point[0]
            if(x**2+y**2>top):
                top = x**2+y**2
                pos = index
        furthest = corners[pos]

        corners = corners.squeeze()
        #Update coordinate system
        corners = furthest - corners 

        #Sort by x
        temp = np.array(sorted(corners, key=lambda tup: tup[0]))

        for col in range(k):
            s = temp[col*k:col*k+k]
            sorted_points.extend(sorted(s, key=lambda tup: tup[1]))
        sorted_points = np.array(sorted_points)

        #Revert coordinate system
        sorted_points = furthest - sorted_points
        return sorted_points

    def extrapolateColoumn(self, sorted_points):
        k = self.k
        sorted_points = list(sorted_points)
        sorted_points_copy = []
        for col in range(k):
            column = sorted_points[col * k:(col + 1) * k]

            p1 = column[0]
            p2 = column[1]

            p3 = column[-1]
            p4 = column[-2]

            distances = (p1[0] - p2[0], abs(p1[1] - p2[1]))
            new_p1 = [p1[0] + distances[0], p1[1] + distances[1]]
            column.insert(0, new_p1)

            distances = (p3[0] - p4[0], abs(p3[1] - p4[1]))
            new_p1 = [p3[0] + distances[0], p3[1] - distances[1]]
            column.append(new_p1)

            sorted_points_copy.extend(column)

        # Visualizing
        temp = cv.imread(self.directory+"/cap.jpg")
        temp = cv.cvtColor(temp, cv.COLOR_BGR2RGB)
        for corner in sorted_points_copy:
            coord = (int(corner[0]), int(corner[1]))
            cv.circle(temp, center=coord, radius=5, color=(0, 255, 0), thickness=5)
        plt.imsave(self.directory+"/extrapolated_coloumn.jpg", temp)

        print("coloumn extrapolated")
        return sorted_points_copy
    
    def extrapolateRow(self, sorted_points):
        newPoints = []
        column1 = sorted_points[0:9]
        column2 = sorted_points[9:18]

        column3 = sorted_points[45:54]
        column4 = sorted_points[54:63]

        column_first = []
        column_last = []

        for i in range(9):
            p1 = column1[i]
            p2 = column2[i]

            p3 = column3[i]
            p4 = column4[i]

            distances = (abs(p1[0] - p2[0]), p1[1] - p2[1])
            new_p1 = [p1[0] + distances[0], p1[1] + distances[1]]

            newPoints.append(new_p1)
            column_first.append(new_p1)

            distances = (abs(p3[0] - p4[0]), p4[1] - p3[1])
            new_p1 = [p4[0] - distances[0], p4[1] + distances[1]]

            newPoints.append(new_p1)
            column_last.append(new_p1)

        column_first.extend(sorted_points)
        column_first.extend(column_last)

        # Visualizing
        temp = cv.imread(self.directory+"/cap.jpg")
        temp = cv.cvtColor(temp, cv.COLOR_BGR2RGB)
        for corner in column_first:
            coord = (int(corner[0]), int(corner[1]))
            cv.circle(temp, center=coord, radius=5, color=(0, 0, 255), thickness=5)
        plt.imsave(self.directory+"/extrapolated_row.jpg", temp)

        print("row extrapolated")
        return column_first
    
    def getChessboardCorners(self,):
        binary_cvt = BinaryConverter()
        img = binary_cvt.convert(self.directory+"/cap.jpg") * 255
        plt.imsave(self.directory+"/bin.jpg", img)
        ret, corners = cv.findChessboardCorners(img, (7, 7),
                                                flags=cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_FAST_CHECK + cv.CALIB_CB_NORMALIZE_IMAGE)
        
        #Visualizing dotted corners
        temp = cv.imread(self.directory+"/cap.jpg")
        temp = cv.cvtColor(temp, cv.COLOR_BGR2RGB)
        if ret:
            for corner in corners:
                coord = (int(corner[0][0]), int(corner[0][1]))
                cv.circle(temp, center=coord, radius=5, color=(255, 0, 0), thickness=5)
        else:
            raise Exception("No chessboard found")
        
        plt.imsave(self.directory+"/dotted.jpg", temp)
        print("corners found")
        return corners
    
    def getCornerBoxes(self, points):
        boxes = {}
        c = ord('A') - 1
        for col in range(8):
            c += 1
            for row in range(8):
                boxes[chr(c) + str(row + 1)] = (points[col * 9 + 1 + 9 + row], points[col * 9 + 1 + row],
                                                points[col * 9 + 9 + row], points[col * 9 + row]) # Top left -> Top right -> Bottom right -> Bottom left
        return boxes

    def calibrate(self, bypass=None):
        print("Calibration starting...")
        boxes = {}

        frame = None
        if(bypass==None):
            _, frame = self.cap.read()
        else:
            frame = cv.imread(bypass)
        cv.imwrite(self.directory+"/cap.jpg", frame)

        #Corners points processing
        corners = self.getChessboardCorners()
        sorted_points = self.sortChessBoardCorners(copy.deepcopy(corners))
        points = self.extrapolateColoumn(sorted_points)
        points = self.extrapolateRow(points)
        boxes = self.getCornerBoxes(points) # Getting chessboard corners boxes (coordinate points)

        print("Done. You can check the results at: "+self.directory)
        return boxes

def main():
    board = Board(bypass="dummy_input/empty1.jpg")

    img = cv.imread("dummy_input/filled1.jpg")
    pred = board.getPiecesPosition(img)
    print(pred)

    return

if __name__ == "__main__":
    main()
