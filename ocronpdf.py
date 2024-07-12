#!/bin/python3
# call like so: ./ocronpdf.py input.pdf en:de:es '_']
#                                  langs    forbidden chars (optional)
# 1. Break pdf into all pages, assuming each page is one page-sized image.
import sys
import subprocess
import glob
process = subprocess.run(['rm pages-*'], shell=True)
process = subprocess.run(['pdfimages', '-all', sys.argv[1], 'pages'])
pages   = sorted(list(glob.glob('pages-*')))

# 2. Apply easyocr to all pages.
import easyocr
reader = easyocr.Reader(lang_list = sys.argv[2].split(":"))
if(len(sys.argv)>3):
    bl=sys.argv[3]
else:
    bl=''
texts = [reader.readtext(file, blocklist=bl) for file in pages]
     
# 3. Rebuild PDF from all pages. 
from fpdf import FPDF # needs fpdf2, not fpdf!
import re

pdf = FPDF()
pdf.set_auto_page_break(False)
pdf.set_text_shaping(True)
pdf.add_font(fname='DejaVuSansCondensed.ttf') # put into the same folder when not found automatically

for page, text in zip(pages, texts):
    # get image resolution to calculate scaling on page
    process = subprocess.run(['identify', page], capture_output=True)
    nums = re.findall(r'\d+', str(process.stdout))
    scaling = float(pdf.eph+pdf.t_margin+pdf.b_margin)/float(nums[2])
    # Append page with image and transparent text overlays
    pdf.add_page()
    pdf.image(page, x=0, y=0, h=pdf.eph+pdf.t_margin+pdf.b_margin)
    for content in text:
        textheight = float(content[0][2][1]-content[0][0][1])*scaling
        textwidth  = float(content[0][1][0]-content[0][0][0])*scaling
        lowerleft  = [float(content[0][0][0])*scaling,float(content[0][0][1])*scaling]
        pdf.set_font('DejaVuSansCondensed', '', int(2.2*textheight)) #size=14)        pdf.set_font('Helvetica', '', int(2.2*textheight))
        with pdf.local_context(fill_opacity=0.0, stroke_opacity=0.0):
            pdf.set_xy(lowerleft[0], lowerleft[1])
            pdf.cell(textwidth,textheight, text = content[1], align = 'C') 

s=sys.argv[1]
pdf.output(s[:-4] + '_ocred' + s[-4:])

