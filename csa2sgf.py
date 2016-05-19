import re, sys, zipfile

class BadFile(Exception): pass

UNICODE_STRING_REGEX = r'UnicodeString="(.+)"'

MOVE_STRING_REGEX = r'([A-Z],[ \d]\d)'




def sgf_point_from_english_string(s, boardsize):        # C17 ---> cc
    if len(s) not in [2,3]:
        return None
    s = s.upper()
    xlookup = " ABCDEFGHJKLMNOPQRSTUVWXYZ"
    try:
        x = xlookup.index(s[0])
    except:
        return None
    try:
        y = boardsize - int(s[1:]) + 1
    except:
        return None
    if 1 <= x <= boardsize and 1 <= y <= boardsize:
        pass
    else:
        return None

    if x < 1 or x > 26 or y < 1 or y > 26:
        return None
    s = ""
    s += chr(x + 96)
    s += chr(y + 96)
    return s


def main():
    if len(sys.argv) < 2:
        print("Usage: {0} <filename>".format(sys.argv[0]))
        print("The filename should be a OXPS file from CrazyStone's Print command")
        exit()

    for zfile in sys.argv[1:]:

        with zipfile.ZipFile(zfile) as arch:

            pages = []

            n = 1
            while True:
                try:
                    decompressed_page = arch.open("Documents/1/Pages/{}.fpage".format(n))
                    pages.append(decompressed_page)
                except:
                    break
                n += 1

            if len(pages) == 0:
                raise BadFile

            lines = []

            for page in pages:
                for line in page:
                    lines.append(line)

            strings = []

            for line in lines:
                extract = re.search(UNICODE_STRING_REGEX, str(line))
                if extract:
                    strings.append(extract.group(1))

            goodstrings = []

            nextstart = 1
            for s in strings:
                startstring = "{} ".format(nextstart)
                if s.startswith(startstring):
                    goodstrings.append(s)
                    nextstart += 1

            sgf = "(;GM[1]FF[4]CA[UTF-8]"
            colour = "B"

            nextstart = 1
            for s in goodstrings:
                startstring = "{} ".format(nextstart)

                # actual_move = s[len(startstring): len(startstring) + 4]

                extract = re.search(MOVE_STRING_REGEX, s)
                if extract:
                    actual_move = extract.group(1)
                    letter = actual_move[0]
                    number = int(actual_move[2:])
                    sgf_move = sgf_point_from_english_string("{}{}".format(letter, number), 19)     # FIXME: currently assuming 19x19

                    sgf += ";{}[{}]".format(colour, sgf_move)

                    colour = "B" if colour == "W" else "W"
                    nextstart += 1

                    extract_2 = re.search(MOVE_STRING_REGEX, s[8:])
                    if extract_2:
                        better_move = extract_2.group(1)
                        letter = better_move[0]
                        number = int(better_move[2:])
                        sgf_move = sgf_point_from_english_string("{}{}".format(letter, number), 19) # FIXME: currently assuming 19x19

                        sgf += "TR[{}]".format(sgf_move)



            sgf += ")"

            outfilename = "{}_analysis.sgf".format(zfile)

            with open(outfilename, "w") as outfile:
                outfile.write(sgf)



main()
