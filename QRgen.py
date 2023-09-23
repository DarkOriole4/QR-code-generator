from reedsolo import RSCodec
from PIL import Image

# given a coordinate in the QR coordinate system, convert to PILs coordinate system
def convert_to_PIL(coor):
    return tuple([SIZE-1 - coor[0], SIZE-1 - coor[1]])

# draw a square locator at a given location (where startpos defines the bottom-right corner of the locator)
def draw_locator(startpos):
    startpos = convert_to_PIL(startpos)
    for y in range(7):
        for x in range(7):
            if y == 0 or y == 6:
                pattern = [0,0,0,0,0,0,0]
            elif y == 1 or  y == 5:
                pattern = [0,1,1,1,1,1,0]
            else:
                pattern = [0,1,0,0,0,1,0]

            pos = [startpos[0] - x, startpos[1] - y]
            qr_code.putpixel(pos, pattern[x])

# this function fills a byte block in the QR code in a given
# direction (down/up), starting from a given point
def fill_byte(data, direction, startpos):
    if len(data) != 8:
        raise Exception("Data block is the wrong length: expected 1 byte")
    elif direction != 'down' and direction != 'up':
        raise Exception("Wrong direction")

    for i in range(8):
        if data[i] == '1':
            x = i % 2
            y = i // 2
            if direction == 'up':
                pos = [startpos[0] + x, startpos[1] + y]
            elif direction == 'down':
                pos = [startpos[0] + x, startpos[1] - y]
            qr_code.putpixel(convert_to_PIL(pos), 0)

# this function returns a requested amount of correction bytes from a given message
def get_parity(msg, ecc):
    if type(msg) != bytes:
        msg = bytearray(msg, "UTF-8")

    rsc = RSCodec(ecc)  # 10 ecc symbols

    # PREPARE MESSAGE
    msg_table = []
    for j in range(len(msg)):
        msg_table.append(msg[j])

    enc_msg = rsc.encode(msg_table)  # generate error corrected message
    parity_str = enc_msg[-ecc:]  # extract the parity bytes

    # CONVERT THE PARITY BYTES TO BINARY
    parity = ''
    for i in range(ecc):
        parity += bin(parity_str[i])[2:].zfill(8)
    return parity

def main():
    ## PARAMETERS
    message = 'Hello!'

    mode = 'byte'     # numeric, alphanumeric, byte, kanji
    mask = 'none'          # masking patterns from 0-7 or 'none'
    err_format = 'M'  # 'L': ~7% restoration, 'M': ~15% restoration, 'Q': ~25% restoration, 'H': ~30% restoration

    ## PREPARE THE PARITY BITS TO PUT INTO THE QR
    if err_format == 'L':
        parity = get_parity(message, 7)
    elif err_format == 'M':
        parity = get_parity(message, 10)
    elif err_format == 'M':
        parity = get_parity(message, 13)
    elif err_format == 'M':
        parity = get_parity(message, 17)
    else:
        raise Exception('Wrong error formatting mode')

    ## INITIALISE THE QR CODE TEMPLATE
    global SIZE
    global qr_code
    SIZE = 21
    qr_code = Image.new(mode="1", size=(SIZE, SIZE), color=1)  # create QR code template (V.1 - 21x21p)

    ## ADD THE MODE DECLARATION
    if mode == 'numeric':
        data = '0001'
    elif mode == 'alphanumeric':
        data = '0010'
    elif mode == 'byte':
        data = '0100'
    elif mode == 'kanji':
        data == '1000'
    else:
        raise Exception('No mode named %s' % (mode))

    for i in range(4):
        if data[i] == '1':
            x = i % 2
            y = i // 2
            qr_code.putpixel(convert_to_PIL((x, y)), 0)


    ## PERFORM THE MASKING
    if mask != 'none':
        for x in range(SIZE):
            for y in range(SIZE):
                if mask == 0:
                    state = (x + y) % 2 == 0
                elif mask == 1:
                    state = x % 2 == 0
                elif mask == 2:
                    state = y % 3 == 0
                elif mask == 3:
                    state = (x + y) % 3 == 0
                elif mask == 4:
                    state = (x/2 + y/3) % 2 == 0
                elif mask == 5:
                    state = (x * y) % 2 + (x * y) % 3 == 0
                elif mask == 6:
                    state = ((x * y) % 3 + x * y) % 2 == 0
                elif mask == 7:
                    state = ((x * y) % 3 + x + y) % 2 == 0
                else:
                    raise Exception('No mask named %s' % (mask))

                if state == True:
                    qr_code.putpixel(convert_to_PIL((x, y)), 0)

    ## INSERT THE SQUARE LOCATORS
    draw_locator((14, 14))
    draw_locator((0, 14))
    draw_locator((14, 0))

    ## DISPLAY THE RESULT
    factor = 52
    qr_code = qr_code.resize(size=(SIZE*factor, SIZE*factor), resample=0)
    qr_code.show()


main()