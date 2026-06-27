import cv2
import numpy as np

img = np.zeros((720, 1280, 3), dtype=np.uint8)
cv2.namedWindow("Test", cv2.WINDOW_AUTOSIZE)
cv2.imshow("Test", img)
rect = cv2.getWindowImageRect("Test")
print("Window rect:", rect)
cv2.waitKey(1)
