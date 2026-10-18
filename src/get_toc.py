import fitz
import sys

def get_toc(pdf_path):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    for item in toc:
        level, title, page = item
        print(f"{'  ' * (level - 1)}- {title} (Page {page})")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        get_toc(sys.argv[1])
    else:
        print("Please provide a PDF path.")
