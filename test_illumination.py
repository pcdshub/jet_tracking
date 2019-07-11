import numpy as np
import cv2

# from cam_utils
def jet_detect(img, x):
    mean = img.mean()
    std = img.std()
    for c in range(x):
        try:
            binary = (img / (mean + 2 * std * 0.90 ** c)).astype(np.uint8)
            lines = cv2.HoughLines(binary, 1, np.radians(0.25), 30)
            rho, theta = lines[0][0]
        except Exception:
            print(c)
            continue
        else:
            # show binary image
            cv2.imshow('binary', binary)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            return rho, theta
    raise ValueError('unable to detect jet')

# get image
# img = cv2.imread('lines.jpg', cv2.IMREAD_GRAYSCALE)
# img = cv2.imread('image.jpeg', cv2.IMREAD_GRAYSCALE)
# img = cv2.imread('white.jpg', cv2.IMREAD_GRAYSCALE)
# img = cv2.imread('black.jpg', cv2.IMREAD_GRAYSCALE)
filename = input("filename: ")
img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)

# show original image
cv2.imshow('image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()

# choose how many times to attempt jet detection
x = int(input("c: "))

rho, theta = jet_detect(img, x)

print(rho)
print(theta)

# draw line on original image
a = np.cos(theta)
b = np.sin(theta)
x0 = a * rho
y0 = b * rho
x1 = int(x0 + 1000 * (-b))
y1 = int(y0 + 1000 * (a))
x2 = int(x0 - 1000 * (-b))
y2 = int(y0 - 1000 * (a))
lined = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
cv2.line(lined, (x1, y1), (x2, y2), (0, 0, 255), 2)

# show binary image
# cv2.imshow('binary', binary)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# save binary image
# cv2.imwrite('images/binary.jpeg', binary)

# show lined image
cv2.imshow('lined', lined)
cv2.waitKey(0)
cv2.destroyAllWindows()

# save lined image
# cv2.imwrite('images/lined.jpeg', lined)
