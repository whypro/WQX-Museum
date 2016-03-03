import os
from PIL import Image

"""Change white backgroud color to green, or change it back."""


filename = '1.bmp'
basename, ext = os.path.splitext(filename)

bak_filename = basename+'.bak'+ext
tmp_filename = basename+'.tmp'+ext

search_pattern = '\xff\xff\xff\x00\x00\x00'
original_pattern = '\xff\xff\xff'
new_pattern = '\x00\xc0\x00'

# os.rename(filename, bak_filename)
has_changed = False
with open(filename, 'rb') as original_file:
    img = Image.open(original_file)
    print img.palette.getdata()
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
        os.unlink(filename)
        os.rename(tmp_filename, filename)

        # os.remove(basename+'.bak'+ext)
#os.rename(tmp_filename, filename)
# os.rename(basename+'.tmp'+ext, filename)
