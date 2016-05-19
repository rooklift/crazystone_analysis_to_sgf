import re, sys, zipfile

class BadFile(Exception): pass

UNICODE_STRING_REGEX = r'UnicodeString="(.+)"'

MOVE_REGEX = r'([A-Z],[ \d]\d)'

OTHER_MOVE_REGEX = r'([A-Z],[ \d]\d)(.*)$'              # needs to be run on only the latter part of the string, else it will get 1st move

SITUATION_REGEX = r'(0\.\d\d\d\d)'


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

            for s in goodstrings:

                # First REGEX

                extract = re.search(MOVE_REGEX, s)
                if extract:
                    actual_move = extract.group(1)
                    letter = actual_move[0]
                    number = int(actual_move[2:])
                    sgf_move = sgf_point_from_english_string("{}{}".format(letter, number), 19)     # FIXME: currently assuming 19x19

                    sgf += ";{}[{}]".format(colour, sgf_move)
                    comment = ""

                    colour = "B" if colour == "W" else "W"

                    # Second REGEX

                    extract = re.search(OTHER_MOVE_REGEX, s[8:])    # Don't start at start so as not to get the first move
                    if extract:
                        better_move = extract.group(1)
                        letter = better_move[0]
                        number = int(better_move[2:])
                        sgf_move = sgf_point_from_english_string("{}{}".format(letter, number), 19) # FIXME: currently assuming 19x19

                        sgf += "TR[{}]".format(sgf_move)

                        delta = extract.group(2)

                        if better_move != actual_move:
                            comment += "CS prefers {}{}".format(letter, number)
                            try:
                                delta_float = float(delta)
                                comment += " -- delta: {:.2f} %\n".format(delta_float * 100)
                            except:
                                comment += "\n"

                    # Third REGEX

                    extract = re.search(SITUATION_REGEX, s)
                    if extract:
                        situation_float = float(extract.group(1))
                        comment += "Black winrate: {:.2f} %\n".format(situation_float * 100)

                    if comment:
                        comment = comment.strip()
                        sgf += "C[{}]".format(comment)

            sgf += ")"

            outfilename = "{}_analysis.sgf".format(zfile)

            with open(outfilename, "w") as outfile:
                outfile.write(sgf)



main()
