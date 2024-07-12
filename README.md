# ocronpdf.py

is a python3 script that ocrs a pdf with a transparent text overlay, assuming one page-sized image per page in portrait orientation.

It requires
- easyocr with all dependencies
- fpdf2 with all dependencies
- imagemagick 
- pdfimages

Works for me, but does not handle edge cases and bad input. Hence it is still simple and malable to your needs, or a starting point for a more elaborate implementation.


