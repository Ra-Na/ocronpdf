# ocronpdf.py

is a python3 script that ocrs a pdf with a transparent text overlay, assuming one page-sized image per page in portrait orientation. Instead of tesseract it uses easyocr.
If you are patient enough to resolve the dependencies and can further take the long ocr and compression times you are rewarded with well compressed, high quality pdfs that are searchable. 

It requires the following tools:
- easyocr 
- jbig2
- fpdf2 (FPDF)
- pymupdf (fitz)
- imagemagick 
- pdftoppm
- the following standard python libraries: sys, os, glob, subprocess, re

Further, it uses the [textcleaner script, http://www.fmwconcepts.com/imagemagick/textcleaner/index.php], which is not included here due to licensing requirements. 
You can use an alternative like unpaper, or download the script yourself.


