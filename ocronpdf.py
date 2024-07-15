#!/bin/python3
import sys
import glob
def usage():
    print("Call like so:   ./ocronpdf.py input.pdf en:de:es dpi '_']")
    print("       languages for ocr, colon-separated_/     /    /   ")
    print("       target dpi, 300 is recommended _________/    /    ")
    print("       optional: forbidden chars between ' in ocr__/     ")
    sys.exit()

captureoutput = True  # set false for debugging info

# Check arguments
if not glob.glob(sys.argv[1]):
    print("Input file not found.")
    usage()
if(len(sys.argv)<4):
    usage()
if(len(sys.argv)>3):
    try: 
        dpi = int(sys.argv[3])
        if dpi<1:
            print("DPI specification errorneous, should be positive.")
            usage()
    except:
        print("DPI specification errorneous, should be an integer.")
        usage()

# 1. Break pdf into all pages, assuming each page is one page-sized image, portrait, A4.
import subprocess
# Clean old files
print("Cleaning up potential garbage.")
process  = subprocess.run(['rm pages-*'], shell=True, capture_output=captureoutput)
process  = subprocess.run(['rm output*'], shell=True, capture_output=captureoutput)
print("Extracting pages.")
process  = subprocess.run(['pdftoppm -png -progress -r '+sys.argv[3]+' '+sys.argv[1]+' pages'], shell=True)  
pages    = sorted(list(glob.glob('pages-*')))
noofpages= len(pages)

# 1.1 Process scans for better ocr-ability.
import os
pagesimp = [page[:-4] + '_improved' + page[-4:] for page in pages]
print("Improving "+str(noofpages)+" pages for better text recognition:")
for page, pageimp in zip(pages, pagesimp):
    print(page+" --> "+pageimp+": ",end='')
    process  = subprocess.run('./textcleaner -e normalize -u -T -s 4 '+page+' '+pageimp, shell=True)
    psize = os.path.getsize(page) 
    pimpsize = os.path.getsize(pageimp) 
    print(str(round(100.0*float(pimpsize-psize)/float(psize),2))+"%")
    if(psize<pimpsize):
        print("Probably an empty page, retaining original file.")
        process = subprocess.run(['cp '+ page + " " + pageimp], shell=True, capture_output=captureoutput)
print(" ")

print("Compressing to png sidecar from jbig2.")
# 1.2 Compress with JBIG2 and retain well-compressed sidecar png, page by page. 
pagesic  = [page[:-4] + '_compressed' + page[-4:] for page in pagesimp]
for pageimp, pageic in zip(pagesimp, pagesic):
    process  = subprocess.run('jbig2 -s -p -O '+pageic+' '+pageimp+' > /dev/null', shell=True, capture_output=captureoutput)
    pimp = os.path.getsize(pageimp) 
    pcmp = os.path.getsize(pageic) 
    print(pageimp+" --> "+pageic+":    "+str(round(100.0*float(pcmp-pimp)/float(pimp),2))+"%")

# 1.3 Compress with JBIG2 for the real deal and, hopefully, create tiny pdf. 
print("Building jbig2 pdf.")
string=''
for item in pagesimp:
    string=string+' '
    string=string+item
process  = subprocess.run('jbig2 -s -p'+string, shell=True)
process  = subprocess.run('python3 pdf.py output > output.pdf', shell=True)

# 2. Apply easyocr to all pages, use improved images.
print("Calling easyocr on all pages.")
import easyocr
reader = easyocr.Reader(lang_list = sys.argv[2].split(":"))
if(len(sys.argv)>4):
    bl=sys.argv[4]
else:
    bl=''
# texts = [reader.readtext(page, blocklist=bl) for page in pagesimp]
texts = []
for index in range(len(pagesimp)):
    print("Page "+str(index+1)+" of "+str(len(pagesimp)))
    texts.append(reader.readtext(pagesimp[index], blocklist=bl))
     
# 3. Rebuild PDF from all pages. 
from fpdf import FPDF # needs fpdf2, not fpdf!
import re

pdf = FPDF()
pdf.set_auto_page_break(False)
pdf.set_text_shaping(True)
pdf.add_font(fname='DejaVuSansCondensed.ttf') # put into the same folder when not found automatically

print("Assembling sidecar pngs and invisible ocr text...")
for page, text in zip(pagesic, texts):
    # get image resolution to calculate scaling on page
    process = subprocess.run(['identify', page], capture_output=True)
    nums = re.findall(r'\d+', str(process.stdout))

    imheight = float(nums[2])
    imwidth = float(nums[1])
    pgheight = float(pdf.eph+pdf.t_margin+pdf.b_margin)
    pgwidth = float(pdf.epw+pdf.l_margin+pdf.r_margin)

    pgar = pgheight/pgwidth
    imar = imheight/imwidth
    
    if(pgar>imar):
        scaling = pgwidth/imwidth
    else:
        scaling = pgheight/imheight
    # Append page with image and transparent text overlays, use improved and compressed images
    pdf.add_page()
    pdf.image(page, x=0, y=0, h = imheight*scaling)
    for content in text:
        textheight = float(content[0][2][1]-content[0][0][1])*scaling
        textwidth  = float(content[0][1][0]-content[0][0][0])*scaling
        lowerleft  = [float(content[0][0][0])*scaling,float(content[0][0][1])*scaling]
        pdf.set_font('DejaVuSansCondensed', '', int(2.2*textheight)) #size=14)        pdf.set_font('Helvetica', '', int(2.2*textheight))
        with pdf.local_context(fill_opacity=0.0, stroke_opacity=0.0):
            pdf.set_xy(lowerleft[0], lowerleft[1])
            pdf.cell(textwidth,textheight, text = content[1], align = 'C') 

s=sys.argv[1]
pdf.output(s[:-4] + '_ocred_PNG' + s[-4:])

# 4.0 Now overlay text on JBIG2-PDF using pymupdf.
print("Inserting invisible ocr text to jbig2 pdf...")
import fitz
doc = fitz.open("output.pdf")

for pageindex in range(len(texts)):
    text = texts[pageindex]
    page = doc[pageindex]
    # get image resolution to calculate scaling on page
    process = subprocess.run(['identify', pages[pageindex]], capture_output=True)
    nums = re.findall(r'\d+', str(process.stdout))

    imheight = float(nums[2])
    imwidth = float(nums[1])
    pgheight = float(pdf.eph+pdf.t_margin+pdf.b_margin)
    pgwidth = float(pdf.epw+pdf.l_margin+pdf.r_margin)

    pgar = pgheight/pgwidth
    imar = imheight/imwidth
    
    if(pgar>imar):
        scaling = pgwidth/imwidth
    else:
        scaling = pgheight/imheight

    scaling = 1 

    for content in text:
        textheight = float(content[0][2][1]-content[0][0][1])*scaling
        textwidth  = float(content[0][1][0]-content[0][0][0])*scaling
        lowerleft  = [float(content[0][0][0])*scaling,float(content[0][0][1])*scaling]
        text_box = page.insert_textbox((lowerleft[0],lowerleft[1],lowerleft[0]+textwidth,lowerleft[1]+textheight), content[1], fontsize=12, fontname='helv', fontfile=None, color=None, fill=None, render_mode=0, border_width=1, expandtabs=8, rotate=0, morph=None, stroke_opacity=0, fill_opacity=0, oc=0, overlay=True)
    page.clean_contents(sanitize=True)

doc.save(s[:-4] + '_ocred_JB2' + s[-4:], deflate=True, clean=True, deflate_images=True, deflate_fonts=True, garbage=4)
doc.close()

print("Cleaning up...")

process  = subprocess.run(['mv output.pdf '+s[:-4] + '_JB2' + s[-4:]], shell=True)

#5 4. Unlike everybody else in this house I CLEAN UP AFTER MYSELF.
process  = subprocess.run(['rm pages-*'], shell=True)
process  = subprocess.run(['rm output.*'], shell=True)

#6 Show some stats.
s = sys.argv[1]
spng = s[:-4] + '_ocred_PNG' + s[-4:]
sjb2 = s[:-4] + '_ocred_JB2' + s[-4:]
size    = os.path.getsize(s) 
sizepng = os.path.getsize(spng) 
sizejb2 = os.path.getsize(sjb2) 
 
print(s   +": "+"          \t"+'{:>12,.0f}'.format(size))
print(spng+": \t"+'{:>12,.0f}'.format(sizepng)+"\t"+str(round(100.0*float(sizepng-size)/float(size),2))+"%")
print(sjb2+": \t"+'{:>12,.0f}'.format(sizejb2)+"\t"+str(round(100.0*float(sizejb2-size)/float(size),2))+"%")

