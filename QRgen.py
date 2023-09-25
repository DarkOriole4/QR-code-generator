from reedsolo import RSCodec
from PIL import Image

## PARAMETERS
message = 'Hello World'
mode = 'alphanumeric' # select mode from: numeric, alphanumeric, byte, kanji
mask = 4              # select masking pattern from 0-7 or 'none'
err_format = 'Q'      # 'L': ~7% restoration, 'M': ~15% restoration, 'Q': ~25% restoration, 'H': ~30% restoration



#converts the full message into the raw alphanumerical bits
def convert_to_anum(message):
    # convert the message into alphanumeric data
    global alphanumeric
    alphanumeric = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:'

    message_data = ''
    message = message.upper()
    for i in range(len(message)):
        if len(message) % 2 != 0 and i == len(message) - 1:  # if the final char is odd
            num1 = anum_ord(message[i])
            block = bin(num1)[2:].zfill(6)
            message_data += block
        elif i % 2 == 0:
            num1 = anum_ord(message[i])
            num2 = anum_ord(message[i + 1])
            block = bin(num1 * 45 + num2)[2:].zfill(11)
            message_data += block
    return message_data


# works like ord() but for alphanumeric encoding
def anum_ord(letter):
    for i in range(len(alphanumeric)):
        if alphanumeric[i] == letter:
            return i
    raise Exception('The character "%s" cannot be encoded' % (letter))


# bitwise xor two binary strings. The result is another string
def bitwise_xor(arg1, arg2):
    if len(arg1) != len(arg2):
        raise Exception('Both arguments need to have the same length')

    result = ''
    for i in range(len(arg1)):
        result += str(int(arg1[i]) ^ int(arg2[i]))
    return result


# draw a square locator at a given location (where startpos defines the bottom-right corner of the locator)
def draw_locator(startpos):
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
                pos = [startpos[0] - x, startpos[1] - y]
            elif direction == 'down':
                pos = [startpos[0] - x, startpos[1] + y]
            qr_code.putpixel(pos, 0)

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
    parity_str = enc_msg[-ecc:]  # cut off the parity bytes

    # CONVERT THE PARITY BYTES TO BINARY
    parity = ''
    for i in range(ecc):
        parity += bin(parity_str[i])[2:].zfill(8)
    return parity


def get_format_parity(message):
    if message == '00000': # edgecase
        return '0000000000' # predefined value

    # generator polynomial taken from the QR code specification
    base_poly = '10100110111'

    # prepare the format string
    message += '0000000000'
    while message[0] == '0':
        message = message[1:]


    # calculate the error correction bits
    while len(message) > 10:
        #pad the generator
        generator = base_poly
        while len(generator) < len(message):
            generator += '0'


        #xor and remove zeros from the left side
        message = bitwise_xor(message, generator)
        while message[0] == '0':
            message = message[1:]

    #pad the remainder on the left
    while len(message) < 10:
        message = '0' + message
    return message



def generate_QR(message, mode, mask, err_format):
    ## PREPARE THE PARITY BITS TO PUT INTO THE QR
    if err_format == 'L':
        main_parity = get_parity(message, 7)
        capacity = 19 * 8 #bits
    elif err_format == 'M':
        main_parity = get_parity(message, 10)
        capacity = 16 * 8 #bits
    elif err_format == 'Q':
        main_parity = get_parity(message, 13)
        capacity = 13 * 8 #bits
    elif err_format == 'H':
        main_parity = get_parity(message, 17)
        capacity = 9 * 8 #bits
    else:
        raise Exception('Wrong error formatting mode')


    ## INITIALISE THE QR CODE TEMPLATE
    global SIZE
    global qr_code
    SIZE = 21
    qr_code = Image.new(mode="1", size=(SIZE, SIZE), color=1)  # create QR code template (V.1 - 21x21p)


    ### ENCODE THE MESSAGE INTO THE QR CODE

    ## GENERATE THE CHARACTER COUNT INDICATOR, MODE DECLARATION AND CONVERT THE DATA INTO BITS
    ## ACCORDING TO THE SELECTED MODE
    if mode == 'numeric':
        mode_data = '0001'
        cci = bin(len(message))[2:].zfill(10)
    elif mode == 'alphanumeric':
        mode_data = '0010'
        cci = bin(len(message))[2:].zfill(9)

        #convert the data
        message_data = mode_data + cci + convert_to_anum(message)
        if len(message_data) > capacity:
            raise Exception('This message is to big (%d bits). Max capacity: %d bits' % (len(message_data), capacity))

    elif mode == 'byte':
        mode_data = '0100'
        cci = bin(len(message))[2:].zfill(8)
    elif mode == 'kanji':
        mode_data == '1000'
        cci = bin(len(message))[2:].zfill(8)
    else:
        raise Exception('No mode named %s' % (mode))


    ## ADD A FEW TERMINATOR BITS TO THE MESSAGE
    if len(message_data) < capacity:
        isFull = False
        for i in range(4):
            if len(message_data) < capacity:
                message_data += '0'
            else:
                isFull = True

        ##  ADD MORE 0'S TO MAKE THE LENGTH A MULTIPLE OF 8
        while len(message_data) % 8 != 0 and isFull == False:
            message_data += '0'
            if len(message_data) == capacity:
                isFull = True

        ## ADD PAD BYTES IF THE STRING IS STILL TOO SHORT
        pad_bytes = ['11101100', '00010001']
        count = 0
        while len(message_data) < capacity:
            message_data += pad_bytes[count % 2]
            count += 1
        isFull = True

        ## COMPLETE THE MESSAGE BY ADDING THE ERROR CORRECTION BYTES AT THE END
        message_data += main_parity
        print(message_data)


    ## PUT THE DATA INTO THE QR CODE
    edges = [20, 9]
    directions = ['up', 'down']

    # draw the first half of data
    for k in range(4):
        # draw a column of bytes
        startpos = [20 - (k * 2), edges[k % 2]]
        for j in range(3):
            if k % 2 == 0:
                pos = [startpos[0], startpos[1] - (j * 4)]
            else:
                pos = [startpos[0], startpos[1] + (j * 4)]

            # draw a byte
            fill_byte(message_data[:8], directions[k % 2], pos)
            message_data = message_data[8:]  # remove the byte that was just written

    #draw the middle section
    startpos = [12, 20]
    for j in range(3):
        pos = [startpos[0], startpos[1] - (j * 4)]
        fill_byte(message_data[:8], 'up', pos)
        message_data = message_data[8:]  # remove the byte that was just written

    #draw the top split section
    startpos = [12, 8]
    for i in range(4):
        if message_data[i] == '1':
            x = i % 2
            y = i // 2
            pos = [startpos[0] - x, startpos[1] - y]
            qr_code.putpixel(pos, 0)
    message_data = message_data[4:]  # remove the 4 bits that were just written

    startpos = [12, 5]
    for i in range(4):
        if message_data[i] == '1':
            x = i % 2
            y = i // 2
            pos = [startpos[0] - x, startpos[1] - y]
            qr_code.putpixel(pos, 0)
    message_data = message_data[4:]  # remove the 4 bits that were just written

    # draw the top section
    pos = [12, 3]
    fill_byte(message_data[:8], 'up', pos)
    message_data = message_data[8:]  # remove the byte that was just written

    pos = [10, 0]
    fill_byte(message_data[:8], 'down', pos)
    message_data = message_data[8:]  # remove the byte that was just written

    #draw the bottom split section
    startpos = [10, 4]
    for i in range(4):
        if message_data[i] == '1':
            x = i % 2
            y = i // 2
            pos = [startpos[0] - x, startpos[1] + y]
            qr_code.putpixel(pos, 0)
    message_data = message_data[4:]  # remove the 4 bits that were just written

    startpos = [10, 7]
    for i in range(4):
        if message_data[i] == '1':
            x = i % 2
            y = i // 2
            pos = [startpos[0] - x, startpos[1] + y]
            qr_code.putpixel(pos, 0)
    message_data = message_data[4:]  # remove the 4 bits that were just written

    # draw the middle section
    startpos = [10, 9]
    for j in range(3):
        pos = [startpos[0], startpos[1] + (j * 4)]
        fill_byte(message_data[:8], 'down', pos)
        message_data = message_data[8:]  # remove the byte that was just written

    # start filling in the left side
    pos = [8, 12]
    fill_byte(message_data[:8], 'up', pos)
    message_data = message_data[8:]  # remove the byte that was just written

    # finish up the left side with the 3 last bytes
    edges = [9, 12]
    directions = ['down', 'up']
    startpos = [5, 9]
    for j in range(3):
        pos = [startpos[0] - (j * 2), edges[k % 2]]
        fill_byte(message_data[:8], directions[k % 2], pos)
        message_data = message_data[8:]  # remove the byte that was just written


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

                # if state == True:
                #     qr_code.putpixel((x, y), 0)


    ## ADD THE STATIC TIMING LINES
    # vertical one
    startpos = [8, 6]
    for i in range(5):
        pos = [startpos[0] + i, startpos[1]]
        qr_code.putpixel(pos, i % 2)

    # horizontal one
    startpos = [6, 8]
    for i in range(5):
        pos = [startpos[0], startpos[1] + i]
        qr_code.putpixel(pos, i % 2)


    ## PREPARE THE ERROR FORMATTING INFO
    if err_format == 'L':
        err_data = '01'
    elif err_format == 'M':
        err_data = '00'
    elif err_format == 'Q':
        err_data = '11'
    elif err_format == 'H':
        err_data = '10'


    ## PREPARE THE MASKING INFO
    if mask == 'none':
        mask_data = '000'
    else:
        mask_data = bin(mask)[2:].zfill(3)


    ## DERIVE THE FORMATTING DATA STRING WITH ERROR-CORRECTION BITS
    format_data = err_data + mask_data
    format_string = format_data + get_format_parity(format_data)

    #xor with a mask taken from the QR code specification
    format_string = bitwise_xor(format_string, '101010000010010')


    ## DRAW THE FORMATTING DATA
    #horizontal line
    startpos = [0, 8]
    count = 0
    for i in range(21):
        #condition required to skip all of the important bits
        if i <= 5 or i == 7 or (i >= 13 and i <= 20):
            if format_string[count] == '1':
                qr_code.putpixel((startpos[0] + i, startpos[1]), 0)
            else:
                qr_code.putpixel((startpos[0] + i, startpos[1]), 1)
            count += 1

    # vertical line
    startpos = [8, 20]
    count = 0
    for i in range(21):
        # condition required to skip all of the important bits
        if i <= 6 or i == 12 or i == 13 or (i >= 15 and i <= 20):
            if format_string[count] == '1':
                qr_code.putpixel((startpos[0], startpos[1] - i), 0)
            else:
                qr_code.putpixel((startpos[0], startpos[1] - i), 1)
            count += 1


    # add the dark module
    qr_code.putpixel((8, 13), 0)


    ## INSERT THE SQUARE LOCATORS
    draw_locator((7, 7))
    draw_locator((21, 7))
    draw_locator((7, 21))


    ## DISPLAY THE RESULT
    factor = 1080 // 21
    qr_code = qr_code.resize(size=(SIZE*factor, SIZE*factor), resample=0)
    qr_code.show()



generate_QR(message, mode, mask, err_format)