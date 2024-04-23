import os
from time import sleep

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np


class MoveDetector:
    cap = None
    boxes = {}
    directory = "output/move_detector"
    prevPos = None
    currentPos = None

    def __init__(self, cam=0):
        self.cap = cv.VideoCapture(cam)
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory)
        self.boxes = self.calibrate()
        return

    def calibrate(self):
        print(
            "Calibrating camera, please put above an empty chessboard and don't move it afterwards.\n Hold for 10 seconds")
        print("------------------------------------------------------------------------------------------")
        sleep(10)
        # Calibrating
        boxes = {}
        _, frame = self.cap.read()
        img = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        img = cv.medianBlur(img, 5)
        ret, th1 = cv.threshold(img, 127, 255, cv.THRESH_BINARY)
        krn = cv.getStructuringElement(cv.MORPH_RECT, (50, 30))
        dlt = cv.dilate(th1, krn, iterations=5)
        res = 255 - cv.bitwise_and(dlt, th1)
        plt.figure(figsize=(10, 10))
        plt.subplot(122)
        plt.imshow(res)

        res = np.uint8(res)
        ret, corners = cv.findChessboardCorners(res, (7, 7),
                                                flags=cv.CALIB_CB_ADAPTIVE_THRESH +
                                                      cv.CALIB_CB_FAST_CHECK +
                                                      cv.CALIB_CB_NORMALIZE_IMAGE)
        temp = frame.copy()
        if ret:
            for corner in corners:
                coord = (int(corner[0][0]), int(corner[0][1]))
                cv.circle(temp, center=coord, radius=5, color=(255, 0, 0), thickness=5)
        else:
            raise Exception("No chessboard found")

        # Sorting
        corners_copy = corners.copy()
        sorted_points = []

        max = -1
        pos = -1
        for index, point in enumerate(corners):
            x, y = point[0]
            if (x ** 2 + y ** 2 > max):
                max = x ** 2 + y ** 2
                pos = index
        poi = corners[pos]
        # Find all pois
        pois = []
        corners_copy = np.ndarray.tolist(corners).copy()
        for index, point in enumerate(corners_copy):
            corners_copy[index] = (index, point[0][0], abs(point[0][1] - poi[0][1]))
        corners_copy.sort(key=lambda a: (a[2], a[1]))

        for i in range(7):
            pois.append(np.ndarray.tolist(corners[corners_copy[i][0]][0]))
        pois.sort(reverse=True)

        for poi in pois:
            col = []
            corners_copy = np.ndarray.tolist(corners).copy()
            for index, point in enumerate(corners_copy):
                corners_copy[index] = (index, abs(point[0][0] - poi[0]), point[0][1])
            corners_copy.sort(key=lambda a: (a[1], a[2]))

            for i in range(0, 7):
                col.append(np.ndarray.tolist(corners[corners_copy[i][0]][0]))
            col.sort(key=lambda a: (a[1], a[0]), reverse=True)

            sorted_points.extend(col)

        # Extrapolating
        # coloumns
        sorted_points_copy = []
        for col in range(7):
            coloumn = sorted_points[col * 7:(col + 1) * 7]

            p1 = coloumn[0]
            p2 = coloumn[1]

            p3 = coloumn[-1]
            p4 = coloumn[-2]

            distances = (abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))
            new_p1 = [p1[0] - distances[0], p1[1] + distances[1]]
            coloumn.insert(0, new_p1)

            distances = (abs(p3[0] - p4[0]), abs(p3[1] - p4[1]))
            new_p1 = [p3[0] + distances[0], p3[1] - distances[1]]
            coloumn.append(new_p1)

            sorted_points_copy.extend(coloumn)

        sorted_points = sorted_points_copy.copy()

        # rows
        newPoints = []
        coloumn1 = sorted_points[0:9]
        coloumn2 = sorted_points[9:18]

        coloumn3 = sorted_points[45:54]
        coloumn4 = sorted_points[54:63]

        coloumn_first = []
        coloumn_last = []

        for i in range(9):
            p1 = coloumn1[i]
            p2 = coloumn2[i]

            p3 = coloumn3[i]
            p4 = coloumn4[i]

            distances = (abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))
            new_p1 = [p1[0] + distances[0], p1[1] + distances[1]]

            newPoints.append(new_p1)
            coloumn_first.append(new_p1)

            distances = (abs(p3[0] - p4[0]), abs(p3[1] - p4[1]))
            new_p1 = [p4[0] - distances[0], p4[1] + distances[1]]

            newPoints.append(new_p1)
            coloumn_last.append(new_p1)

        coloumn_first.extend(sorted_points)
        coloumn_first.extend(coloumn_last)

        sorted_points = coloumn_first.copy()

        temp = frame.copy()
        for corner in sorted_points:
            coord = (int(corner[0]), int(corner[1]))
            cv.circle(temp, center=coord, radius=5, color=(255, 0, 255), thickness=5)
        plt.subplot(121)
        plt.imshow(temp)

        c = ord('A') - 1
        for col in range(8):
            c += 1
            for row in range(8):
                boxes[chr(c) + str(row + 1)] = (sorted_points[col * 9 + 1 + 9 + row], sorted_points[col * 9 + 1 + row],
                                                sorted_points[col * 9 + 9 + row], sorted_points[col * 9 + row])

        plt.savefig(self.directory + '/out.jpg', dpi=1000)
        plt.close()

        print("Done :). Images stored in:\n" + self.directory + "/out.jpg")
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
        return values[0][1], values[1][1]

    def detectPiece(self):
        newImg = cv.absdiff(self.currentPos, self.prevPos)
        return self.findTop2(self.boxes, newImg)


def main():
    detector = MoveDetector()
    print("sleeping")
    sleep(50)
    detector.takePicture()
    print("done")
    print("sleeping")
    sleep(10)
    print("done")
    detector.takePicture()
    print(detector.detectPiece())
    return


main()
