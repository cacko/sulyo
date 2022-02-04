#!/usr/bin/env python
from traceback import print_exc
from PIL import Image, ImageDraw, ImageFont
import os, sys, getopt

def main(argv):
    output_filename = "output.png" #default output filename
    code = ""
    try:
        opts, args = getopt.getopt(argv,"i:o:",[])
    except getopt.GetoptError:
        print("Usage: text2image -i input.txt -o output_name.png")
        sys.exit(2)
    # for opt, arg in opts:
    #     if opt == '-i':
    #         fo = open(arg, "r")
    #         lines = fo.readlines()
    #         for line in lines:
    #             tab_to_space_line = line.replace('\t', '    ')
    #             code += tab_to_space_line
    #         fo.close()
    #         os.remove(arg)
    #     elif opt == '-o':
    #         output_filename = arg

    code = """
    
    """
    im = Image.new('RGBA', (1200, 600), (48, 10, 36, 255)) #background like Ubuntu
    draw = ImageDraw.Draw(im)
    try:
        monoFont = ImageFont.truetype(font='./SourceCodePro-Medium.ttf', size=42)
        print(monoFont)
        draw.text((50, 10), code, fill='white', font=monoFont)
    except Exception as ex:
        print_exc(ex)
        draw.text((10, 10), code, fill='white')
    im.save(output_filename)
    
s = """      𝚃𝚒𝚖𝚎        𝙴𝚟𝚎𝚗𝚝                                        
𝟷𝟿∶𝟹𝟶  𝙶𝙼𝚃    𝙷𝙴𝚁𝚃𝙷𝙰  𝚅𝚂  𝙱𝙾𝙲𝙷𝚄𝙼                  
𝟷𝟿∶𝟺𝟻  𝙶𝙼𝚃    𝙱𝙸𝚁𝙼𝙸𝙽𝙶𝙷𝙰𝙼  𝚅𝚂  𝚂𝙷𝙴𝙵𝙵𝙸𝙴𝙻𝙳  𝚄
𝟸𝟶∶𝟶𝟶  𝙶𝙼𝚃    𝙼𝙰𝙽  𝚄𝙽𝙸𝚃𝙴𝙳  𝚅𝚂  𝙼𝙸𝙳𝙳𝙻𝙴𝚂𝙱𝚁𝙾𝚄
𝟸𝟶∶𝟶𝟶  𝙶𝙼𝚃    𝙶𝙴𝚃𝙰𝙵𝙴  𝚅𝚂  𝙻𝙴𝚅𝙰𝙽𝚃𝙴  """

if __name__ == "__main__":
    main(s)
