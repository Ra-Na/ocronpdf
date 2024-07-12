# ocronpdf.py

is a python3 script that ocrs a pdf with a transparent text overlay, assuming one page-sized image per page in portrait orientation. Instead of tesseract it uses easyocr.

It requires
- easyocr with all dependencies
- fpdf2 with all dependencies
- imagemagick 
- pdfimages

Works for me, but does not handle edge cases, landscape images, bad input and whatnot. Expect belly-landings which are easy to fix, since the script is rather simple and malable to your needs. Alternatives are ocrmypdf if you prefer tesseract.

