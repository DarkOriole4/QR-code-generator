from reedsolo import RSCodec
from PIL import Image
import math

## PARAMETERS
message = 'Hello World'
mode = 'alphanumeric' # select mode from: numeric, alphanumeric, byte, kanji
err_format = 'Q'      # 'L': ~7% restoration, 'M': ~15% restoration, 'Q': ~25% restoration, 'H': ~30% restoration
SIZE = 21             # determines the QR codes version (only V1: SIZExSIZE for now)

show_info = False
mask_override = False
mask = 2             # select masking pattern from 0-7 or 'none'


def evaluate_qr(qr_code):
    penalty = 0
    dark_count = 0

    ## RULE NO 1
    #horizontal
    prev_val = 0
    for y in range(SIZE):
        line_len = 0  # reset line
        for x in range(SIZE):
            val = qr_code.getpixel((x,y))

            if val == 0:         # count up the dark modules
                dark_count += 1  # for rule no 4

            #back to rule no 1
            if prev_val != val:
                line_len = 1 # reset line
            else:
                line_len += 1 # same line

            if line_len == 5: # unwanted length
                penalty += 3
            elif line_len > 5: # further penalties
                penalty += 1
            prev_val = val

    # vertical
    prev_val = 0
    for x in range(SIZE):
        line_len = 0  # reset line
        for y in range(SIZE):
            val = qr_code.getpixel((x, y))

            if prev_val != val:
                line_len = 1  # reset line
            else:
                line_len += 1  # same line

            if line_len == 5:  # unwanted length
                penalty += 3
            elif line_len > 5:  # further penalties
                penalty += 1
            prev_val = val
    if show_info == True:
        print("horizontal + vertical lines:", penalty)

    ## RULE NO 2
    penalty2 = 0
    for y in range(SIZE - 1):
        for x in range(SIZE - 1):
            # iterate through a 2x2 square where the top left corner is at (x, y)
            isIllegal = True
            root_val = qr_code.getpixel((x, y))
            for i in range(1, 4):
                val = qr_code.getpixel((x + i % 2, y + i // 2))
                if val != root_val:
                    isIllegal = False

            if isIllegal:
                penalty2 += 3
    if show_info == True:
        print("2x2 squares:", penalty2)

    ## RULE NO 3
    penalty3 = 0
    illegal_lines = ["01000101111", "11110100010"]

    # horizontally
    for y in range(SIZE):
        for x in range(11):
            for i in range(11): #for each bit in the forbidden line 1...
                if qr_code.getpixel((x+i, y)) != int(illegal_lines[0][i]):
                    break
                elif i == 10 and qr_code.getpixel((x+i, y)) == int(illegal_lines[0][10]):
                    penalty3 += 40

            for i in range(11): #for each bit in the forbidden line 2...
                if qr_code.getpixel((x+i, y)) != int(illegal_lines[1][i]):
                    break
                elif i == 10 and qr_code.getpixel((x+i, y)) == int(illegal_lines[1][10]):
                    penalty3 += 40

    # vertically
    for x in range(SIZE):
        for y in range(11):
            for i in range(11):  # for each bit in the forbidden line 1...
                if qr_code.getpixel((x, y + i)) != int(illegal_lines[0][i]):
                    break
                elif i == 10 and qr_code.getpixel((x, y + i)) == int(illegal_lines[0][10]):
                    penalty3 += 40

            for i in range(11):  # for each bit in the forbidden line 2...
                if qr_code.getpixel((x, y + i)) != int(illegal_lines[1][i]):
                    break
                elif i == 10 and qr_code.getpixel((x, y + i)) == int(illegal_lines[1][10]):
                    penalty3 += 40
    if show_info == True:
        print("forbidden lines:", penalty3)

    ## RULE NO 4
    percent = math.ceil((dark_count / SIZE ** 2) * 100)
    prev_percent = percent
    next_percent = percent
    if percent % 5 != 0:
        while next_percent % 5 != 0:
            next_percent += 1
        while prev_percent % 5 != 0:
            prev_percent -= 1

    prev_percent = abs(prev_percent - 50)
    next_percent = abs(next_percent - 50)

    if prev_percent < next_percent:
        penalty4 = prev_percent * 2
    else:
        penalty4 = next_percent * 2
    if show_info == True:
        print("B/W ratio:", penalty4)

    return penalty + penalty2 + penalty3 + penalty4


#converts the full message into the raw alphanumerical bits
def convert_to_anum(message):
    # convert the message into alphanumeric data
    global alphanumeric
    alphanumeric = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:'

    mesg_data = ''
    message = message.upper()
    for i in range(len(message)):
        if len(message) % 2 != 0 and i == len(message) - 1:  # if the final char is odd
            num1 = anum_ord(message[i])
            block = bin(num1)[2:].zfill(6)
            mesg_data += block
        elif i % 2 == 0:
            num1 = anum_ord(message[i])
            num2 = anum_ord(message[i + 1])
            block = bin(num1 * 45 + num2)[2:].zfill(11)
            mesg_data += block
    return mesg_data


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
            if pos[0] <= SIZE - 1 and pos[0] >= 0 and pos[1] <= SIZE - 1 and pos[1] >= 0:
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
    if type(msg) != bytes and type(msg) != list:
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

    ## INITIALISE THE QR CODE TEMPLATE
    global qr_code
    qr_code = Image.new(mode="1", size=(SIZE, SIZE), color=1)  # create QR code template (V.1 - SIZExSIZEp)


    ### ENCODE THE MESSAGE INTO THE QR CODE

    ## DEFINE THE CAPACITY OF THE QR CODE
    if err_format == 'L':
        capacity = 19 * 8 #bits
    elif err_format == 'M':
        capacity = 16 * 8 #bits
    elif err_format == 'Q':
        capacity = 13 * 8 #bits
    elif err_format == 'H':
        capacity = 9 * 8 #bits
    else:
        raise Exception('Wrong error formatting mode')

    ## generate the character count indicator, mode declaration and convert the data
    # into bits according to the selected mode
    if mode == 'numeric':
        mode_data = '0001'
        cci = bin(len(message))[2:].zfill(10)
    elif mode == 'alphanumeric':
        mode_data = '0010'
        cci = bin(len(message))[2:].zfill(9)

        #convert the data
        mesg_data = mode_data + cci + convert_to_anum(message)
        if len(mesg_data) > capacity:
            raise Exception('This message is to big (%d bits). Max capacity: %d bits' % (len(mesg_data), capacity))

    elif mode == 'byte':
        mode_data = '0100'
        cci = bin(len(message))[2:].zfill(8)
    elif mode == 'kanji':
        mode_data == '1000'
        cci = bin(len(message))[2:].zfill(8)
    else:
        raise Exception('No mode named %s' % (mode))


    ## ADD A FEW TERMINATOR BITS TO THE MESSAGE
    if len(mesg_data) < capacity:
        isFull = False
        for i in range(4):
            if len(mesg_data) < capacity:
                mesg_data += '0'
            else:
                isFull = True

        ##  ADD MORE 0'S TO MAKE THE LENGTH A MULTIPLE OF 8
        while len(mesg_data) % 8 != 0 and isFull == False:
            mesg_data += '0'
            if len(mesg_data) == capacity:
                isFull = True

        ## ADD PAD BYTES IF THE STRING IS STILL TOO SHORT
        pad_bytes = ['11101100', '00010001']
        count = 0
        while len(mesg_data) < capacity:
            mesg_data += pad_bytes[count % 2]
            count += 1
        isFull = True

        ## CALCULATE THE ERROR_CORRECTION BITS
        tmp = []
        word = ''
        for i in range(len(mesg_data)):
            if i % 8 == 0 and i != 0:
                tmp.append(int(word, 2))
                word = ''
                word += mesg_data[i]
            elif i == len(mesg_data) - 1:
                word += mesg_data[i]
                tmp.append(int(word, 2))
            else:
                word += mesg_data[i]

        if err_format == 'L':
            main_parity = get_parity(tmp, 7)
        elif err_format == 'M':
            main_parity = get_parity(tmp, 10)
        elif err_format == 'Q':
            main_parity = get_parity(tmp, 13)
        elif err_format == 'H':
            main_parity = get_parity(tmp, 17)


        ## COMPLETE THE MESSAGE BY ADDING THE ERROR CORRECTION BYTES AT THE END
        mesg_data += main_parity


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
            fill_byte(mesg_data[:8], directions[k % 2], pos)
            mesg_data = mesg_data[8:]  # remove the byte that was just written

    #draw the middle section
    startpos = [12, 20]
    for j in range(3):
        pos = [startpos[0], startpos[1] - (j * 4)]
        fill_byte(mesg_data[:8], 'up', pos)
        mesg_data = mesg_data[8:]  # remove the byte that was just written

    #draw the top split section
    startpos = [12, 8]
    for i in range(4):
        if mesg_data[i] == '1':
            x = i % 2
            y = i // 2
            pos = [startpos[0] - x, startpos[1] - y]
            qr_code.putpixel(pos, 0)
    mesg_data = mesg_data[4:]  # remove the 4 bits that were just written

    startpos = [12, 5]
    for i in range(4):
        if mesg_data[i] == '1':
            x = i % 2
            y = i // 2
            pos = [startpos[0] - x, startpos[1] - y]
            qr_code.putpixel(pos, 0)
    mesg_data = mesg_data[4:]  # remove the 4 bits that were just written

    # draw the top section
    pos = [12, 3]
    fill_byte(mesg_data[:8], 'up', pos)
    mesg_data = mesg_data[8:]  # remove the byte that was just written

    pos = [10, 0]
    fill_byte(mesg_data[:8], 'down', pos)
    mesg_data = mesg_data[8:]  # remove the byte that was just written

    #draw the bottom split section
    startpos = [10, 4]
    for i in range(4):
        if mesg_data[i] == '1':
            x = i % 2
            y = i // 2
            pos = [startpos[0] - x, startpos[1] + y]
            qr_code.putpixel(pos, 0)
    mesg_data = mesg_data[4:]  # remove the 4 bits that were just written

    startpos = [10, 7]
    for i in range(4):
        if mesg_data[i] == '1':
            x = i % 2
            y = i // 2
            pos = [startpos[0] - x, startpos[1] + y]
            qr_code.putpixel(pos, 0)
    mesg_data = mesg_data[4:]  # remove the 4 bits that were just written

    # draw the middle section
    startpos = [10, 9]
    for j in range(3):
        pos = [startpos[0], startpos[1] + (j * 4)]
        fill_byte(mesg_data[:8], 'down', pos)
        mesg_data = mesg_data[8:]  # remove the byte that was just written

    # start filling in the left side
    pos = [8, 12]
    fill_byte(mesg_data[:8], 'up', pos)
    mesg_data = mesg_data[8:]  # remove the byte that was just written

    # finish up the left side with the 3 last bytes
    edges = [9, 12]
    directions = ['down', 'up']
    startpos = [5, 9]
    for j in range(3):
        pos = [startpos[0] - (j * 2), edges[k % 2]]
        fill_byte(mesg_data[:8], directions[k % 2], pos)
        mesg_data = mesg_data[8:]  # remove the byte that was just written


    ## PERFORM THE MASKING
    if mask != 'none':
        for x in range(SIZE):
            for y in range(SIZE):
                if mask == 0:
                    state = (x + y) % 2 == 0
                elif mask == 1:
                    state = y % 2 == 0
                elif mask == 2:
                    state = x % 3 == 0
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

                if state == True and mask != 'none':
                    px_val = qr_code.getpixel((x,y))
                    qr_code.putpixel((x, y), px_val ^ 1)


    ## MANUAL AND DIRTY BUG FIX
    # fix area #1
    for i in range(10, 12):
        x, y = [0, i]
        px_val = qr_code.getpixel((x, y))
        qr_code.putpixel((x, y), px_val ^ 1)

    # fix area #2
    for i in range(9, 13):
        x, y = [5, i]
        px_val = qr_code.getpixel((x, y))
        qr_code.putpixel((x, y), px_val ^ 1)

    # fix area 3 (bottom)
    for i in range(18, 21, 2):
        x, y = [11, i]
        px_val = qr_code.getpixel((x, y))
        qr_code.putpixel((x, y), px_val ^ 1)

    for i in range(18, 21):
        x, y = [12, i]
        px_val = qr_code.getpixel((x, y))
        qr_code.putpixel((x, y), px_val ^ 1)


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
    for i in range(SIZE):
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
    for i in range(SIZE):
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
    draw_locator((SIZE, 7))
    draw_locator((7, SIZE))

    return qr_code


if mask_override == False:
    ## EVALUATE ALL OF THE MASKS AND CHOOSE THE BEST ONE
    best = [999, 999]  # mode, penalty
    for mask in range(8):
        qr_code = generate_QR(message, mode, mask, err_format)
        penalty = evaluate_qr(qr_code)
        if show_info == True:
            print("\nmask", mask)
            print("total:", penalty)
        if penalty < best[1]:
            best = [mask, penalty, qr_code]

    qr_code = best[2]
    if show_info == True:
        print("\nBEST MASK:", best[0])
else:
    qr_code = generate_QR(message, mode, mask, err_format)

## ADD THE QUIET ZONE
margin_size = 2
final_qr = Image.new(mode="1", size=(SIZE + margin_size*2, SIZE + margin_size*2), color=1)
final_qr.paste(qr_code, (margin_size, margin_size))


## DISPLAY THE RESULT
factor = 1080 // SIZE
final_qr = final_qr.resize(size=(SIZE*factor, SIZE*factor), resample=0)
final_qr.show()