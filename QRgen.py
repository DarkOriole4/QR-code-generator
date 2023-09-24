from reedsolo import RSCodec
from PIL import Image

# given a coordinate in the QR coordinate system, convert to PILs coordinate system
def convert_to_PIL(coor):
    return tuple([SIZE-1 - coor[0], SIZE-1 - coor[1]])

# draw a square locator at a given location (where startpos defines the bottom-right corner of the locator)
def draw_locator(startpos):
    startpos = convert_to_PIL(startpos)
    for y in range(9):
        for x in range(9):
            if y == 0 or y == 8:
                pattern = [0,0,0,0,0,0,0,0,0]
            if y == 1 or y == 7:
                pattern = [0,1,1,1,1,1,1,1,0]
            elif y == 2 or  y == 6:
                pattern = [0,1,0,0,0,0,0,1,0]
            elif y >= 3 and y <= 5:
                pattern = [0,1,0,1,1,1,0,1,0]

            pos = [startpos[0] - x, startpos[1] - y]
            if pos[0] <= 20 and pos[0] >= 0 and pos[1] <= 20 and pos[1] >= 0:
                if pattern[x] == 1:
                    qr_code.putpixel(pos, 0)
                elif pattern[x] == 0:
                    qr_code.putpixel(pos, 1)

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
    message = 'Hello World!'

    mode = 'byte'     # numeric, alphanumeric, byte, kanji
    mask = 4          # masking patterns from 0-7 or 'none' (4 might be a bit buggy)
    err_format = 'L'  # 'L': ~7% restoration, 'M': ~15% restoration, 'Q': ~25% restoration, 'H': ~30% restoration


    ## PREPARE THE PARITY BITS TO PUT INTO THE QR
    if err_format == 'L':
        main_parity = get_parity(message, 7)
    elif err_format == 'M':
        main_parity = get_parity(message, 10)
    elif err_format == 'Q':
        main_parity = get_parity(message, 13)
    elif err_format == 'H':
        main_parity = get_parity(message, 17)
    else:
        raise Exception('Wrong error formatting mode')


    ## INITIALISE THE QR CODE TEMPLATE
    global SIZE
    global qr_code
    SIZE = 21
    qr_code = Image.new(mode="1", size=(SIZE, SIZE), color=1)  # create QR code template (V.1 - 21x21p)


    ## ENCODE THE MODE DECLARATION
    if mode == 'numeric':
        mode_data = '0001'
    elif mode == 'alphanumeric':
        mode_data = '0010'
    elif mode == 'byte':
        mode_data = '0100'
    elif mode == 'kanji':
        mode_data == '1000'
    else:
        raise Exception('No mode named %s' % (mode))

    for i in range(4):
        if mode_data[i] == '1':
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
                    state = (x//3 + y//2) % 2 == 0
                elif mask == 5:
                    state = (x * y) % 2 + (x * y) % 3 == 0
                elif mask == 6:
                    state = (((x * y) % 2) + (x * y) % 3) % 2 == 0
                elif mask == 7:
                    state = (((x + y) % 2) + ((x * y) % 3)) % 2 == 0
                else:
                    raise Exception('No mask named %s' % (mask))

                if state == True:
                    qr_code.putpixel(convert_to_PIL((x, y)), 0)


    ## ENCODE THE MASKING
    if mask == 0 or mask == 'none':
        mask_data = '000'
    elif mask == 1:
        mask_data = '001'
    elif mask == 2:
        mask_data = '010'
    elif mask == 3:
        mask_data = '011'
    elif mask == 4:
        mask_data = '100'
    elif mask == 5:
        mask_data = '101'
    elif mask == 6:
        mask_data = '110'
    elif mask == 7:
        mask_data = '111'

    # vertical one
    startpos = [12, 2]
    for i in range(3):
        pos = [startpos[0], startpos[1] + i]
        if mask_data[i] == '1':
            qr_code.putpixel(convert_to_PIL(pos), 0)
        elif mask_data[i] == '0':
            qr_code.putpixel(convert_to_PIL(pos), 1)

    # horizontal one
    startpos = [18, 12]
    for i in range(3):
        pos = [startpos[0] - i, startpos[1]]
        if mask_data[i] == '1':
            qr_code.putpixel(convert_to_PIL(pos), 0)
        elif mask_data[i] == '0':
            qr_code.putpixel(convert_to_PIL(pos), 1)


    ## ADD THE STATIC TEMPLATE LINES
    # vertical one
    startpos = (12, 14)
    for i in range(5):
        pos = [startpos[0] - i, startpos[1]]
        qr_code.putpixel(convert_to_PIL(pos), i % 2)

    # horizontal one
    startpos = [14, 12]
    for i in range(5):
        pos = [startpos[0], startpos[1] - i]
        qr_code.putpixel(convert_to_PIL(pos), i % 2)


    ## ENCODE THE ERROR FORMATTING
    if err_format == 'L':
        err_data = '01'
    elif err_format == 'M':
        err_data = '00'
    elif err_format == 'Q':
        err_data = '11'
    elif err_format == 'H':
        err_data = '10'

    # vertical one
    startpos = [12, 0]
    for i in range(2):
        pos = [startpos[0], startpos[1] + i]
        if err_data[i] == '1':
            qr_code.putpixel(convert_to_PIL(pos), 0)
        elif err_data[i] == '0':
            qr_code.putpixel(convert_to_PIL(pos), 1)

    # horizontal one
    startpos = [20, 12]
    for i in range(2):
        pos = [startpos[0] - i, startpos[1]]
        if err_data[i] == '1':
            qr_code.putpixel(convert_to_PIL(pos), 0)
        elif err_data[i] == '0':
            qr_code.putpixel(convert_to_PIL(pos), 1)


    ##ERROR CORRECTION BITS FOR THE FORMATTING DATA
    format_data = err_data + mask_data
    format_parity = get_parity(format_data, 1)
    print(format_parity)


    ## INSERT THE SQUARE LOCATORS
    draw_locator((13, 13))
    draw_locator((-1, 13))
    draw_locator((13, -1))


    ## DISPLAY THE RESULT
    factor = 52
    qr_code = qr_code.resize(size=(SIZE*factor, SIZE*factor), resample=0)
    qr_code.show()


main()