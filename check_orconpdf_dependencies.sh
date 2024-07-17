#!/bin/bash
declare -a arr=("easyocr" "img2pdf" "jbig2" "pdftoppm" "pngcrush" "pymupdf")

exitstat=0

RED='\033[0;31m'
NC='\033[0m' 
for i in "${arr[@]}"
do
    if ! command -v $i &> /dev/null
    then
        printf "${RED}$i could not be found!${NC}\n"
        exitstat=1
    else 
        echo "$i is present."
    fi
done
exit $exitstat