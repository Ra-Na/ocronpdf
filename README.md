# ocronpdf.py

is a python3 script that ocrs a pdf with a transparent text overlay, treating each page as a single image. Instead of tesseract it uses easyocr. A png- and a jb2-encoded pdf are generated. If you are patient enough to resolve the dependencies and can further take the long ocr and compression times, you are rewarded with well compressed, high quality pdfs that are searchable. 

It requires python3 and the following tools:
- easyocr 
- jbig2
- pngcrush
- pymupdf (fitz)
- imagemagick 
- pdftoppm
- standard python libraries: sys, os, glob, subprocess, re
- for parallel processing: awk, pdfinfo

Other dependencies: 
- If found, it uses a [textcleaner script](http://www.fmwconcepts.com/imagemagick/textcleaner/index.php) for ocr preprocessing, which is not included here due to licensing requirements. 
You can use an alternative like unpaper, or download the script yourself like so:
`curl 'http://www.fmwconcepts.com/imagemagick/downloadcounter.php?scriptname=textcleaner&dirname=textcleaner' > textcleaner`
`chmod +x textcleaner`
- It includes `pdf.py` from [image-to-jbig2-pdf](https://github.com/2m/image-to-jbig2-pdf/tree/master) to assemble a pdf from the jbig2-compressed images.

# How?
Download `check_orconpdf_dependencies.sh`, `ocronpdf.py`, `pdf.py`, make them executable and run `ocronpdf.py`.

# Why?
If you have it but you can't find it, you have no advantage over not having it. Scanned PDFs should be indexed and searchable. I recommend combining your PDF collection with [recoll](https://www.recoll.org/index.html) to quickly find anyting you actually have. 

# To do 
- Better error handling
- Rudimentary dependency checks are in place, but there is no minimum version checking
