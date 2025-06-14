# Import necessary libraries
from PIL import Image
import pytesseract 

# Set the Tesseract path for Windows ( comment this line if using other operating systems )
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'   

# Load the image
image_path = '../sample images/sample 15.jpg' # Replace with your image file path
image = Image.open(image_path)

# Perform OCR i.e. extract text from image
extracted_text = pytesseract.image_to_string(image)

# Print the result
print("Extracted Text:\n", extracted_text)