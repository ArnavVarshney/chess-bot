import os
from time import sleep
import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
from util import BinaryConverter


class MoveDetector:
    cap = None
    boxes = {}
    directory = "output/move_detector"
    prevPos = None
    currentPos = None
    translation = {"A": "H", "H": "A", "B": "G", "G": "B", "C": "F", "F": "C", "D": "E", "E": "D"}

    def __init__(self, cam=0):
        # self.cap = cv.VideoCapture(cam)
        # self.cap.set(3, 1920)
        # self.cap.set(4, 1080)
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory)
        self.boxes = self.calibrate()
        return

    def calibrate(self):
        boxes = {}

        # _, frame = self.cap.read()
        frame = cv.imread("empty_test.jpg")
        cv.imwrite(self.directory+"/cap.jpg", frame)

        binary_cvt = BinaryConverter()
        img = binary_cvt.convert(self.directory+"/cap.jpg")

        ret, corners = cv.findChessboardCorners(img*255, (7, 7),
                                                flags=cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_FAST_CHECK + cv.CALIB_CB_NORMALIZE_IMAGE)
        
        #Visualizing dotted corners
        temp = frame.copy()
        if ret:
            for corner in corners:
                coord = (int(corner[0][0]), int(corner[0][1]))
                cv.circle(temp, center=coord, radius=5, color=(255, 0, 0), thickness=5)
        else:
            raise Exception("No chessboard found")
        
        plt.imsave(self.directory+"/dotted.jpg", temp)

        # Sorting
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

        for col in range(7):
            s = temp[col*7:col*7+7]
            sorted_points.extend(sorted(s, key=lambda tup: tup[1]))
        sorted_points = np.array(sorted_points)

        #Revert coordinate system
        sorted_points = furthest - sorted_points

        # Extrapolating
        # columns
        sorted_points = list(sorted_points)
        sorted_points_copy = []
        for col in range(7):
            column = sorted_points[col * 7:(col + 1) * 7]

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

        sorted_points = sorted_points_copy.copy()

        # rows
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

        sorted_points = column_first.copy()

        # Visualizing
        temp = frame.copy()
        for corner in sorted_points:
            coord = (int(corner[0]), int(corner[1]))
            cv.circle(temp, center=coord, radius=5, color=(255, 0, 255), thickness=5)
        plt.imsave(self.directory+"/dotted2.jpg", temp)

        c = ord('A') - 1
        for col in range(8):
            c += 1
            for row in range(8):
                boxes[chr(c) + str(row + 1)] = (sorted_points[col * 9 + 1 + 9 + row], sorted_points[col * 9 + 1 + row],
                                                sorted_points[col * 9 + 9 + row], sorted_points[col * 9 + row])

        print("Done :)")
        return boxes

    def takePicture(self):
        _, frame = self.cap.read()
        self.prevPos = self.currentPos
        self.currentPos = frame

    def tileSum(self, bound, img):
        coords = []
        for i in bound:
            coord = (int(i[0]), int(i[1]))
            coords.append(coord)
            cv.circle(img, center=coord, radius=5, color=(255, 0, 0), thickness=5)

        # print(coords[0][0], coords[3][0] , coords[0][1], coords[3][1])
        bound1 = min(coords[0][0], coords[3][0])
        bound2 = max(coords[0][0], coords[3][0])
        bound3 = min(coords[0][1], coords[3][1])
        bound4 = max(coords[0][1], coords[3][1])
        tile = img[bound3:bound4, bound1:bound2]

        return tile.sum()

    def findTop2(self, boxes, img):
        values = []
        for box in boxes:
            sum = self.tileSum(boxes[box], img)
            values.append((sum, box))
        values.sort(reverse=True)
        return self.translation[values[0][1][0]].lower() + values[0][1][1], self.translation[values[1][1][0]].lower() + \
               values[1][1][1]

    def detectPiece(self):
        newImg = cv.absdiff(self.currentPos, self.prevPos)
        return self.findTop2(self.boxes, newImg)


def main():
    detector = MoveDetector()
    # print("sleeping")
    # sleep(15)
    # detector.takePicture()
    # print("done")
    # print("sleeping")
    # sleep(10)
    # print("done")
    # detector.takePicture()
    # print(detector.detectPiece())
    return


if __name__ == "__main__":
    main()
