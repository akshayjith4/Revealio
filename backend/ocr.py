import pytesseract
import sys
import os
from PIL import Image
from rapidfuzz.distance import Levenshtein

def character_accuracy(ground_truth, ocr_output):
    """Calculate character-level accuracy using Levenshtein distance."""
    distance = Levenshtein.distance(ground_truth, ocr_output)
    accuracy = (1 - distance / max(len(ground_truth), 1)) * 100
    return round(accuracy, 2)

def word_accuracy(ground_truth, ocr_output):
    """Calculate word-level accuracy by comparing extracted words."""
    gt_words = ground_truth.split()
    ocr_words = ocr_output.split()
    correct_words = sum(1 for word in ocr_words if word in gt_words)
    accuracy = (correct_words / max(len(gt_words), 1)) * 100
    return round(accuracy, 2)

def extract_text(image_path, ground_truth=""):
    """Extract text from an image using Tesseract OCR and print accuracy."""
    try:
        # Load image using Pillow
        image = Image.open(image_path)
        
        # Perform OCR
        extracted_text = pytesseract.image_to_string(image).strip()

        print("\n=== Extracted Text ===\n")
        print(extracted_text)

        # Convert RGBA to RGB if needed before saving
        if image.mode in ["RGBA", "P"]:
            image = image.convert("RGB")

        # Save a copy of the processed image
        processed_image_path = os.path.splitext(image_path)[0] + "_saved.jpg"
        image.save(processed_image_path, format="JPEG")

        print("\n[INFO] Processed Image saved at:", processed_image_path)

        # Calculate accuracy if ground truth is provided
        if ground_truth:
            char_acc = character_accuracy(ground_truth, extracted_text)
            word_acc = word_accuracy(ground_truth, extracted_text)
            print(f"\n📊 [ACCURACY] Character-Level: {char_acc}% | Word-Level: {word_acc}%\n")

        return extracted_text, processed_image_path
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None, None

if __name__ == "__main__":
    """Handle command-line arguments"""
    if len(sys.argv) > 2:
        image_path = sys.argv[1]
        ground_truth = sys.argv[2]  # Provide correct text as input
    else:
        image_path = "sample1.jpg"  # Default image
        ground_truth = ""  # No ground truth provided by default

    extracted_text, processed_image_path = extract_text(image_path, ground_truth)
