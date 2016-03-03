# -*- coding: utf-8 -*- 
import os
from PIL import Image

for root, dirs, files in os.walk('.'):
    for file in files:
        filename = os.path.join(root, file)
        basename, ext = os.path.splitext(file)

        if ext != '.bmp':
            continue
        # print os.path.join(root, filename).encode('utf-8')

        bak_filename = os.path.join(root, basename+'.bak'+ext)
        tmp_filename = os.path.join(root, basename+'.tmp'+ext)

        search_pattern = '\xff\xff\xff\x00\x00\x00'
        original_pattern = '\xff\xff\xff'
        new_pattern = '\x00\xc0\x00'

        # os.rename(filename, bak_filename)
        has_changed = False
        with open(filename, 'rb') as original_file:
            img = Image.open(original_file)
            try:
                print img.palette.getdata()
            except AttributeError:
                original_file.close()
                continue
            rawmode, data = img.palette.getdata()
            if data.startswith(search_pattern):
                new_data = data.replace(original_pattern, new_pattern, 1)
                img.putpalette(new_data, rawmode)
                with open(tmp_filename, 'wb') as new_file:
                    img.save(new_file)
                    new_file.close()
                has_changed = True
                print 'has_changed'
            original_file.close()
            if has_changed:
                os.rename(filename, bak_filename)
                os.rename(tmp_filename, filename)
