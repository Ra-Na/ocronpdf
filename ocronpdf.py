#!/bin/python3
import sys
import glob
import time
start_time = time.time()

def usage(enforce):
    print("Call like so:   ./ocronpdf.py input.pdf en:de:es DPI '<_|>' dfrppp")
    print("                                /           /     /    /    / ")
    print("input pdf______________________/           /     /    /    /  ")
    print("language(s) for ocr, colon-separated______/     /    /    /   ")
    print("target dpi, 300 is recommended ________________/    /    /    ")
    print("forbidden ocr chars between apostrophes, may be ''_/    /     ")
    print("optional, unset by default, no spaces__________________/      ")
    print("   d = debug output                                           ")
    print("   f = force continue even on errors                          ")
    print("   r = retain image files (don't cleanup)                     ")
    print("   ppp = parallel processing on 3 processes (extrapolate)     ")
    print("         gives minor speedup on image processing on large pdfs")
    print("         but no gain for ocr")
    
    if(not enforce):
        sys.exit(-1)
    else:
        print("Continuing anyway, good luck.")

captureoutput = True # prevents console output from other scripts, set False for debugging info or use "d"-option
debug = False # set True or use "d"-option

inparallel = False

enforce = False

cleanup = True # set False to retain image files or use "r"-option

# 0.0 Check arguments 
if len(sys.argv)<5:
    print("\033[93m"+"Arguments missing."+"\033[0m")
    usage(False)
# arg 1 - pdf
if not glob.glob(sys.argv[1]):
    print("Input file not found.")
    usage(False)
else: 
    infile = sys.argv[1]
    pngpdf = infile[:-4] + '_ocred_PNG' + infile[-4:]
    jb2pdf = infile[:-4] + '_ocred_JB2' + infile[-4:]
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
        usage(False)
except:
    print("DPI should be a positive integer.")
    usage(False)
# arg 4
bl = sys.argv[4]
# set options, if any
if(len(sys.argv) >= 6):
    optionstring = sys.argv[5]
    if('d' in optionstring):
        captureoutput = False
        debug = True
    if('r' in optionstring):
        cleanup = False
    if('f' in optionstring):
        enforce = True
    if('p' in optionstring):
        cpus = optionstring.count('p')
        if cpus>1:
            inparallel = True
            print("Using "+str(cpus)+" parallel processes.")
            from concurrent.futures import ProcessPoolExecutor
            def my_parallel_command(command):
                subprocess.run(command, shell=True)
            def my_parallel_command_capture_output(command):
                subprocess.run(command, shell=True, capture_output=True)
                        
if(debug):
    print("Arguments seem to be OK.")

import subprocess
# 0.1 check dependencies
proc = subprocess.run('./check_orconpdf_dependencies.sh', shell=True, capture_output=captureoutput)
if(proc.returncode != 0):
    print("Dependencies not met!")
    print(proc.stdout.decode())
    if(not enforce):
        sys.exit(-1)
    else:
        print("Continuing anyway, good luck.")


# 0.2 Clean old files
print("Cleaning up potential garbage.")
process  = subprocess.run(['rm pages-*'], shell=True, capture_output=captureoutput)
process  = subprocess.run(['rm output*'], shell=True, capture_output=captureoutput)

# 1.0 Break pdf into individual pages, assuming each page is one page-sized image, portrait, A4. 
#     This is like virtual printing. Do not use pdfimages -> belly-lands when a page contains multiple images. 
print("Extracting pages.")
if inparallel == False:
    process  = subprocess.run(['pdftoppm -png -progress -r '+sys.argv[3]+' '+sys.argv[1]+' pages'], shell=True)  
    pages    = sorted(list(glob.glob('pages-*')))
    noofpages= len(pages)
else: 
    proc = subprocess.run('pdfinfo '+infile+' | grep Pages  | awk \'{print $2}\'', shell=True,capture_output=True)
    noofpages = int(proc.stdout.decode())
    commands = ["pdftoppm -png -progress -r "+sys.argv[3]+" -f "+str(i+1)+" -l "+str(i+1)+" "+infile+" " + "pages" for i in range(noofpages)]
    with ProcessPoolExecutor(max_workers = cpus) as executor:
        futures = executor.map(my_parallel_command, commands)
    pages = sorted(list(glob.glob('pages-*')))

# 2.0 Process scans for better ocr-ability.
import os
pages_improved = [page[:-4] + '_improved' + page[-4:] for page in pages]

if glob.glob("textcleaner"):
    print("Improving "+str(noofpages)+" pages for better text recognition. Here(*) you may want to hand-pick some options.")
    if(inparallel==False):
        for page, page_improved in zip(pages, pages_improved):
            print(page+" --> "+page_improved+": ",end='')
            process  = subprocess.run('./textcleaner -e normalize -u -T -s 4 '+page+' '+page_improved, shell=True)
            psize = os.path.getsize(page) 
            pimpsize = os.path.getsize(page_improved) 
            print(str(round(100.0*float(pimpsize-psize)/float(psize),2))+"%")
            if(psize<pimpsize):
                print("Probably an empty page, copying original file.")
                process = subprocess.run(['cp '+ page + " " + page_improved], shell=True, capture_output=captureoutput)
    else:
        commands = ['./textcleaner -e normalize -u -T -s 4 '+pages[i]+' '+pages_improved[i] for i in range(noofpages)]
        with ProcessPoolExecutor(max_workers = cpus) as executor:
            futures = executor.map(my_parallel_command, commands)
        for page, page_improved in zip(pages, pages_improved):
            psize = os.path.getsize(page) 
            pimpsize = os.path.getsize(page_improved) 
            print(page+" --> "+page_improved+": "+str(round(100.0*float(pimpsize-psize)/float(psize),2))+"%")
            if(psize<pimpsize):
                print("Probably an empty page, copying original file.")
                process = subprocess.run(['cp '+ page + " " + page_improved], shell=True, capture_output=captureoutput)

else:
    print("\033[93m"+"Here(***) you might want to add some preprocessing steps for better ocr. I recommend you do")
    print("curl 'http://www.fmwconcepts.com/imagemagick/downloadcounter.php?scriptname=textcleaner&dirname=textcleaner' > textcleaner")
    print("chmod +x textcleaner")
    print("before the next run. 'textcleaner' is not included here due to licensing requirements: it is fine for private use but")
    print("redistribution or commercial use needs the author's consent. Alternatives are unpaper, scantailor, or scripting with")
    print("imagemagick or gimp or python's openCV (https://www.dynamsoft.com/codepool/deskew-scanned-document.html).")
    print("For now I just copy the files."+"\033[0m")
    for page, page_improved in zip(pages, pages_improved):
        process = subprocess.run(['cp '+ page + " " + page_improved], shell=True, capture_output=captureoutput)

# 3.0 Compression effort. Compress with JBIG2 for the real deal and, hopefully, create tiny pdf. 
print("Assembling pdf from jbig2s.")
string=''
for item in pages_improved:
    string=string+' '
    string=string+item
process = subprocess.run('jbig2 -s -p'+string, shell=True)
print("")
process = subprocess.run('python3 pdf.py output > output.pdf', shell=True)

# 3.1 Build tiny PDF from png files. 
#     First compress with JBIG2 and retain sidecar png, page by page. 
#     The compression is awesome but lossy. We further reduce the png size with pngcrush.
#     Then, assemble pdf.
print("Building png pdf:")
print("|_1: Compressing to png sidecar from jbig2 and applying pngcrush.")
pages_improved_compressed  = [page[:-4] + '_compressed' + page[-4:] for page in pages_improved]
if inparallel==False:
    for page_improved, page_improved_compressed in zip(pages_improved, pages_improved_compressed):
        process  = subprocess.run('jbig2 -s -p -O '+'output.tmp.png '+page_improved+' > /dev/null', shell=True, capture_output=captureoutput)
        process  = subprocess.run("pngcrush -l 9 output.tmp.png " + page_improved_compressed, shell=True, capture_output=captureoutput)
        pimp = os.path.getsize(page_improved) 
        pcmp = os.path.getsize(page_improved_compressed) 
        print("|    "+page_improved+" --> "+page_improved_compressed+":    "+str(round(100.0*float(pcmp-pimp)/float(pimp),2))+"%")
else: 
    pages_tmp = [page[:-4] + '_tmp' + page[-4:] for page in pages_improved]
    commands = ['jbig2 -s -p -O '+pages_tmp[i]+' ' +pages_improved[i]+' > /dev/null' for i in range(noofpages)]
    with ProcessPoolExecutor(max_workers = cpus) as executor:
        futures = executor.map(my_parallel_command_capture_output, commands)
    commands = ['pngcrush -l 9 '+pages_tmp[i]+ " " + pages_improved_compressed[i] for i in range(noofpages)]
    with ProcessPoolExecutor(max_workers = cpus) as executor:
        futures = executor.map(my_parallel_command_capture_output, commands)
    for page_improved, page_improved_compressed in zip(pages_improved, pages_improved_compressed):
        pimp = os.path.getsize(page_improved) 
        pcmp = os.path.getsize(page_improved_compressed) 
        print("|    "+page_improved+" --> "+page_improved_compressed+":    "+str(round(100.0*float(pcmp-pimp)/float(pimp),2))+"%")

print("\\_2: Assembling pdf from pngs.")
string=''
for item in pages_improved_compressed:
    string=string+' '
    string=string+item
print("\033[93m") # highlight potential warning output from img2pdf
process = subprocess.run('img2pdf'+string+" --engine=internal -o output.png.pdf", shell=True)
print("\033[0m")
# 4.0 Apply easyocr.
print("Applying easyocr to improved, uncompressed pages. Here(**) you may want to hand-pick some options.")
import easyocr
reader = easyocr.Reader(lang_list = langlist)
# texts = [reader.readtext(page, blocklist=bl) for page in pages_improved] # changed to stuff below for progress indication
texts = []
for index in range(len(pages_improved)):
    print("Page "+str(index+1)+" of "+str(len(pages_improved)))
#    if inparallel == True:
#        texts.append(reader.readtext(pages_improved[index], blocklist=bl, workers=cpus))
#    else:
    texts.append(reader.readtext(pages_improved[index], blocklist=bl))

# 5.0 Now overlay text on PDFs using pymupdf.
fontsize = 12
print("Inserting invisible ocr text to jbig2 and png pdfs.")
import fitz
doc = fitz.open("output.pdf")
doc2 = fitz.open("output.png.pdf")
scaling = 72.0/dpi
for pageindex in range(len(texts)):
    text = texts[pageindex]
    page = doc[pageindex]
    page2 = doc2[pageindex]
    for content in text:
        textheight = float(content[0][2][1]-content[0][0][1])
        textwidth  = float(content[0][1][0]-content[0][0][0])
        lowerleft  = [float(content[0][0][0]),float(content[0][0][1])]
        page.insert_textbox((lowerleft[0],lowerleft[1],lowerleft[0]+textwidth,lowerleft[1]+textheight), content[1], fontsize=fontsize, fontname='helv', fontfile=None, color=None, fill=None, render_mode=0, border_width=1, expandtabs=8, rotate=0, morph=None, stroke_opacity=0, fill_opacity=0, oc=0, overlay=True)
        page2.insert_textbox((lowerleft[0]*scaling,lowerleft[1]*scaling,lowerleft[0]*scaling+textwidth*scaling,lowerleft[1]*scaling+textheight*scaling), content[1], fontsize=int(fontsize*scaling), fontname='helv', fontfile=None, color=None, fill=None, render_mode=0, border_width=1, expandtabs=8, rotate=0, morph=None, stroke_opacity=0, fill_opacity=0, oc=0, overlay=True)
    page.clean_contents(sanitize=True)
    page2.clean_contents(sanitize=True)

doc.save(jb2pdf, deflate=True, clean=True, deflate_images=True, deflate_fonts=True, garbage=4)
doc.close()
doc2.save(pngpdf, deflate=True, clean=True, deflate_images=True, deflate_fonts=True, garbage=4)
doc2.close()

# 6.0  Unlike everybody else in this house I CLEAN UP AFTER MYSELF.
if cleanup:
    print("Cleaning up.")
    process  = subprocess.run(['rm pages-*'], shell=True)
    process  = subprocess.run(['rm output.*'], shell=True)

# 7.0 Show some stats and exit gracefully.

sizeori = os.path.getsize(infile)/1024 
sizepng = os.path.getsize(pngpdf)/1024 
sizejb2 = os.path.getsize(jb2pdf)/1024 
 
print('\033[92m'+infile   +": "+"          "+'{:>8,.0f}'.format(sizeori)+" KB")
print(pngpdf+": "+'{:>8,.0f}'.format(sizepng)+" KB"+"  "+str(round(100.0*float(sizepng-sizeori)/float(sizeori),2))+" %")
print(jb2pdf+": "+'{:>8,.0f}'.format(sizejb2)+" KB"+"  "+str(round(100.0*float(sizejb2-sizeori)/float(sizeori),2))+" %"+'\033[0m')
print("--- %s seconds ---" % int(time.time() - start_time))
sys.exit(0)


# To do:
# - Error handling
# - Dependency checking / version checking
# - Documentation


######### Alternative method of assembling the PDF with ocr overlay
# I replaced fpdf usage by pymupdf usage. Pymupdf can handle JB2, unlike fpdf, so both variants are
# ocr-overlaid in one go. If for whatever reason you want to use fpdf, here is the code:

# # 3.0 Rebuild PDF from all pages. 
# from fpdf import FPDF # needs fpdf2, not fpdf!
# import re
# 
# pdf = FPDF()
# pdf.set_auto_page_break(False)
# pdf.set_text_shaping(True)
# pdf.add_font(fname='DejaVuSansCondensed.ttf') # put into the same folder when not found automatically
# 
# print("Assembling sidecar pngs and invisible ocr text. V1")
# for page, text in zip(pages_improved_compressed, texts):
#     # get image resolution to calculate scaling on page
#     process = subprocess.run(['identify', page], capture_output=True)
#     nums = re.findall(r'\d+', str(process.stdout))
# 
#     imheight = float(nums[2])
#     imwidth = float(nums[1])
#     pgheight = float(pdf.eph+pdf.t_margin+pdf.b_margin)
#     pgwidth = float(pdf.epw+pdf.l_margin+pdf.r_margin)
# 
#     pgar = pgheight/pgwidth
#     imar = imheight/imwidth
#     
#     if(pgar>imar):
#         scaling = pgwidth/imwidth
#     else:
#         scaling = pgheight/imheight
#     # Append page with image and transparent text overlays, use improved and compressed images
#     pdf.add_page()
#     pdf.image(page, x=0, y=0, h = imheight*scaling)
#     for content in text:
#         textheight = float(content[0][2][1]-content[0][0][1])*scaling
#         textwidth  = float(content[0][1][0]-content[0][0][0])*scaling
#         lowerleft  = [float(content[0][0][0])*scaling,float(content[0][0][1])*scaling]
#         pdf.set_font('DejaVuSansCondensed', '', int(2.2*textheight)) #size=14)        pdf.set_font('Helvetica', '', int(2.2*textheight))
#         with pdf.local_context(fill_opacity=0.0, stroke_opacity=0.0):
#             pdf.set_xy(lowerleft[0], lowerleft[1])
#             pdf.cell(textwidth,textheight, text = content[1], align = 'C') 
# 
# s=sys.argv[1]
# pdf.output(s[:-4] + '_ocred_PNG' + s[-4:])

