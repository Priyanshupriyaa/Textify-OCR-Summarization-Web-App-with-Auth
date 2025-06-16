import sys
from ocr_summarizer import preprocess_image, extract_text, summarize_text

def test_ocr(image_path):
    preprocessed = preprocess_image(image_path)
    text = extract_text(preprocessed)
    print("Extracted Text:")
    print(text)
    summary = summarize_text(text)
    print("\nSummary:")
    print(summary)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_ocr_run.py <image_path>")
        sys.exit(1)
    image_path = sys.argv[1]
    test_ocr(image_path)
