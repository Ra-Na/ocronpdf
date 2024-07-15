# ocronpdf.py

is a python3 script that ocrs a pdf with a transparent text overlay, assuming one page-sized image per page in portrait orientation. Instead of tesseract it uses easyocr. A png- and a jb2-encoded pdf are generated. If you are patient enough to resolve the dependencies and can further take the long ocr and compression times, you are rewarded with well compressed, high quality pdfs that are searchable. 

It requires the following tools:
- easyocr 
- jbig2
- fpdf2 (FPDF)
- pymupdf (fitz)
- imagemagick 
- pdftoppm
- standard python libraries: sys, os, glob, subprocess, re

Other dependencies: 
- It uses a [textcleaner script](http://www.fmwconcepts.com/imagemagick/textcleaner/index.php), which is not included here due to licensing requirements. 
You can use an alternative like unpaper, or download the script yourself like so:
`curl 'http://www.fmwconcepts.com/imagemagick/downloadcounter.php?scriptname=textcleaner&dirname=textcleaner' > textcleaner`
`chmod +x textcleaner`
- It includes `pdf.py` from [image-to-jbig2-pdf](https://github.com/2m/image-to-jbig2-pdf/tree/master) to assemble a pdf from the jbig2-compressed images.


