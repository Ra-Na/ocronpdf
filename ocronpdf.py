#!/bin/python3
import sys
import glob
def usage():
    print("Call like so:   ./ocronpdf.py input.pdf en:de:es DPI '<_|>' dr")
    print("                                /           /     /    /    / ")
    print("input pdf______________________/           /     /    /    /  ")
    print("language(s) for ocr, colon-separated______/     /    /    /   ")
    print("target dpi, 300 is recommended ________________/    /    /    ")
    print("forbidden ocr chars between apostrophes, may be ''_/    /     ")
    print("optional, unset by default:____________________________/      ")
    print("   d = debug output                                           ")
    print("   r = retain image files (don't cleanup)                     ")
    sys.exit(-1)

captureoutput = True # prevents console output from other scripts, set False for debugging info or use "d"-option
cleanup = True # set False to retain image files or use "r"-option
debug = False # set True or use "d"-option

# To do:
# - Error handling
# - Dependency checking / version checking
# - Parallelization
# - Documentation
# - Replace fpdf usage by pymupdf usage. Pymupdf can handle JB2, unlike fpdf.

# 0.0 Check arguments 
if len(sys.argv)<5:
    print("\033[93m"+"Arguments missing."+"\033[0m")
    usage()
# arg 1 - pdf
if not glob.glob(sys.argv[1]):
    print("Input file not found.")
    usage()
# arg 2 - language codes
valid_lang_codes = {'abq','ady','af','ang','ar','as','ava','az','be','bg','bh','bho','bn','bs','ch_sim','ch_tra','che','cs','cy','da','dar','de','en','es','et','fa','fr','ga','gom','hi','hr','hu','id','inh','is','it','ja','kbd','kn','ko','ku','la','lbe','lez','lt','lv','mah','mai','mi','mn','mr','ms','mt','ne','new','nl','no','oc','pi','pl','pt','ro','ru','rs_cyrillic','rs_latin','sck','sk','sl','sq','sv','sw','ta','tab','te','th','tjk','tl','tr','ug','uk','ur','uz','vi'}
langlist = sys.argv[2].split(":")
if not set(langlist) <= valid_lang_codes:
    print("Supplied language codes not supported by easyocr (2024-07). Offending input: ", set(langlist).difference(valid_lang_codes))
    sys.exit(-1)
# arg 3 - DPI
try: 
    dpi = int(sys.argv[3])
    if dpi<1:
        print("DPI should be positive.")
        usage()
except:
    print("DPI should be a positive integer.")
    usage()
# arg 4
bl = sys.argv[4]
# 
if(len(sys.argv) >= 6):
    optionstring = sys.argv[5]
    if('d' in optionstring):
        captureoutput = False
        debug = True
    if('r' in optionstring):
        cleanup = False

if(debug):
    print("Arguments _seem_ to be OK.")

import subprocess
# 0.2 Clean old files
print("Cleaning up potential garbage.")
process  = subprocess.run(['rm pages-*'], shell=True, capture_output=captureoutput)
process  = subprocess.run(['rm output*'], shell=True, capture_output=captureoutput)
# 0.3 Break pdf into individuall pages, assuming each page is one page-sized image, portrait, A4. 
#     This is like virtual printing. Do not use pdfimages -> belly-lands when a page contains multiple images. 
print("Extracting pages.")
process  = subprocess.run(['pdftoppm -png -progress -r '+sys.argv[3]+' '+sys.argv[1]+' pages'], shell=True)  
pages    = sorted(list(glob.glob('pages-*')))
noofpages= len(pages)

# 1.1 Process scans for better ocr-ability.
import os
pagesimp = [page[:-4] + '_improved' + page[-4:] for page in pages]

if glob.glob("textcleaner"):
    print("Improving "+str(noofpages)+" pages for better text recognition. Here(*) you may want to hand-pick some options.")
    for page, pageimp in zip(pages, pagesimp):
        print(page+" --> "+pageimp+": ",end='')
        process  = subprocess.run('./textcleaner -e normalize -u -T -s 4 '+page+' '+pageimp, shell=True)
        psize = os.path.getsize(page) 
        pimpsize = os.path.getsize(pageimp) 
        print(str(round(100.0*float(pimpsize-psize)/float(psize),2))+"%")
        if(psize<pimpsize):
            print("Probably an empty page, copying original file.")
            process = subprocess.run(['cp '+ page + " " + pageimp], shell=True, capture_output=captureoutput)
else:
    print("\033[93m"+"Here(***) you might want to add some preprocessing steps for better ocr. I recommend you do")
    print("curl 'http://www.fmwconcepts.com/imagemagick/downloadcounter.php?scriptname=textcleaner&dirname=textcleaner' > textcleaner")
    print("chmod +x textcleaner")
    print("before the next run. 'textcleaner' is not included here due to licensing requirements: it is fine for private use but")
    print("redistribution or commercial use needs the author's consent. Alternatives are unpaper, scantailor, or scripting with")
    print("imagemagick or gimp or python's openCV (https://www.dynamsoft.com/codepool/deskew-scanned-document.html).")
    print("For now I just copy the files."+"\033[0m")
    for page, pageimp in zip(pages, pagesimp):
        process = subprocess.run(['cp '+ page + " " + pageimp], shell=True, capture_output=captureoutput)

print("Compressing to png sidecar from jbig2.")
# 1.2 Compress with JBIG2 and retain well-compressed sidecar png, page by page. 
#     The compression is awesome but lossy. We further reduce the png size with pngcrush.
pagesic  = [page[:-4] + '_compressed' + page[-4:] for page in pagesimp]
for pageimp, pageic in zip(pagesimp, pagesic):
#    process  = subprocess.run('jbig2 -s -p -O '+pageic+' '+pageimp+' > /dev/null', shell=True, capture_output=captureoutput)
    process  = subprocess.run('jbig2 -s -p -O '+'output.tmp.png '+pageimp+' > /dev/null', shell=True, capture_output=captureoutput)
    process  = subprocess.run("pngcrush -l 9 output.tmp.png " + pageic, shell=True, capture_output=captureoutput)
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

# 2.0 Apply easyocr.
print("Applying easyocr to improved, uncompressed pages. Here(**) you may want to hand-pick some options.")
import easyocr
reader = easyocr.Reader(lang_list = langlist)
# texts = [reader.readtext(page, blocklist=bl) for page in pagesimp] # changed to stuff below for progress indication
texts = []
for index in range(len(pagesimp)):
    print("Page "+str(index+1)+" of "+str(len(pagesimp)))
    texts.append(reader.readtext(pagesimp[index], blocklist=bl))
     
# 3.0 Rebuild PDF from all pages. 
from fpdf import FPDF # needs fpdf2, not fpdf!
import re

pdf = FPDF()
pdf.set_auto_page_break(False)
pdf.set_text_shaping(True)
pdf.add_font(fname='DejaVuSansCondensed.ttf') # put into the same folder when not found automatically

print("Assembling sidecar pngs and invisible ocr text.")
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
print("Inserting invisible ocr text to jbig2 pdf.")
import fitz
doc = fitz.open("output.pdf")

for pageindex in range(len(texts)):
    text = texts[pageindex]
    page = doc[pageindex]
    for content in text:
        textheight = float(content[0][2][1]-content[0][0][1])
        textwidth  = float(content[0][1][0]-content[0][0][0])
        lowerleft  = [float(content[0][0][0]),float(content[0][0][1])]
        text_box = page.insert_textbox((lowerleft[0],lowerleft[1],lowerleft[0]+textwidth,lowerleft[1]+textheight), content[1], fontsize=12, fontname='helv', fontfile=None, color=None, fill=None, render_mode=0, border_width=1, expandtabs=8, rotate=0, morph=None, stroke_opacity=0, fill_opacity=0, oc=0, overlay=True)
    page.clean_contents(sanitize=True)

doc.save(s[:-4] + '_ocred_JB2' + s[-4:], deflate=True, clean=True, deflate_images=True, deflate_fonts=True, garbage=4)
doc.close()

# 5.0  Unlike everybody else in this house I CLEAN UP AFTER MYSELF.
if cleanup:
    print("Cleaning up.")
    process  = subprocess.run(['rm pages-*'], shell=True)
    process  = subprocess.run(['rm output.*'], shell=True)

# 6.0 Show some stats and exit gracefully.
s = sys.argv[1]
spng = s[:-4] + '_ocred_PNG' + s[-4:]
sjb2 = s[:-4] + '_ocred_JB2' + s[-4:]
size    = os.path.getsize(s)/1024 
sizepng = os.path.getsize(spng)/1024 
sizejb2 = os.path.getsize(sjb2)/1024 
 
print('\033[92m'+s   +": "+"          "+'{:>8,.0f}'.format(size)+" KB")
print(spng+": "+'{:>8,.0f}'.format(sizepng)+" KB"+"  "+str(round(100.0*float(sizepng-size)/float(size),2))+" %")
print(sjb2+": "+'{:>8,.0f}'.format(sizejb2)+" KB"+"  "+str(round(100.0*float(sizejb2-size)/float(size),2))+" %"+'\033[0m')
sys.exit(1)


