import cv2 as cv
import scipy.signal
import numpy as np

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

def resize(imgs, size=100):
    imgs = list(imgs)
    for i in range(len(imgs)):
        img = imgs[i]
        imgs[i] = cv.resize(img, (size,size))

    return np.array(imgs)

def splitAndSwap(imgs):
    imgs = list(imgs)
    for i in range(len(imgs)):
        img = imgs[i]
        temp = list(cv.split(img))
        _ = temp[2].copy()
        temp[2] = temp[0].copy()
        temp[0] = _ 

        imgs[i] = temp
    
    return np.array(imgs)