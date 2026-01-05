from pdfminer.high_level import extract_text
import sys
import os

# Usage: python pdf2txt_extract.py <pdf_path>
def pdf_to_txt(pdf_path):
    if not pdf_path.lower().endswith('.pdf'):
        print('Input file must be a PDF.')
        return
    txt_path = os.path.splitext(pdf_path)[0] + '.txt'
    text = extract_text(pdf_path)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Extracted text saved to {txt_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python pdf2txt_extract.py <pdf_path>')
        sys.exit(1)
    pdf_to_txt(sys.argv[1]) 