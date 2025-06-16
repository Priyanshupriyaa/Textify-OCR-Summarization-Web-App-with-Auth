import cv2
import pytesseract
import numpy as np

image_path = 'test.jpeg'
image = cv2.imread(image_path)

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply Otsu thresholding (binary image with black text on white bg)
_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# OPTIONAL: Slight dilation to enhance clarity (for printed text)
kernel = np.ones((2, 2), np.uint8)
processed = cv2.dilate(thresh, kernel, iterations=1)

# OCR config: Use PSM 4 (block of text), OEM 3 (default LSTM engine)
custom_config = r'--oem 3 --psm 4'

# Extract text
text = pytesseract.image_to_string(processed, config=custom_config)
print(text)

# View processed image (for debugging)
cv2.imshow("Processed", processed)
cv2.waitKey(0)
cv2.destroyAllWindows()
