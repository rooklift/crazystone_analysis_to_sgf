# CrazyStone Analysis to SGF
# https://github.com/fohristiwhirl/crazystone_analysis_to_sgf
#
# The problem: CrazyStone Deep Learning 1.0 (released 2016-05-16) can analyse a game but the only output
# is via printing its "Record Analysis List" from the Print menu. Fortunately, you can usually "print" it
# to an XPS or OXPS file.
#
# Such files are actually just zip-compressed directories that contain some other files. So conversion to
# an SGF is just a matter of reading the right files in the archive and using the info contained therein.
#
# Usage: Arguments are generally considered to be filenames, except you can also do --size 9 (or whatever).
# The same board size is used for every input file. Size 19 is used by default.

import codecs, re, sys, zipfile

HOTSPOT_DELTA = 0.04    # Hotspot (sgf: "HO[1]") if delta >= this

class BadFile(Exception): pass

UNICODE_STRING_REGEX = r'UnicodeString="(.+)"'
MOVE_REGEX = r'([A-Z],[ \d]\d)'
OTHER_MOVE_REGEX = r'([A-Z],[ \d]\d)(.*)$'              # needs to be run on only the latter part of the string, else it will get 1st move
SITUATION_REGEX = r'(0\.\d\d\d\d)'


def sgf_point_from_english_string(s, boardsize):        # "C17" ---> "cc"
    if len(s) not in [2,3]:
        raise ValueError
    s = s.upper()
    xlookup = " ABCDEFGHJKLMNOPQRSTUVWXYZ"
    x = xlookup.index(s[0])                             # Could raise ValueError
    y = boardsize - int(s[1:]) + 1                      # Could raise ValueError
    return sgf_point_from_point(x, y)


def sgf_point_from_point(x, y):                         # 3, 3 --> "cc"
    if x < 1 or x > 26 or y < 1 or y > 26:
        raise ValueError
    s = ""
    s += chr(x + 96)
    s += chr(y + 96)
    return s


def handicap_points(boardsize, handicap, tygem = False):

    points = set()

    if boardsize < 4:
        return points

    if handicap > 9:
        handicap = 9

    if boardsize < 13:
        d = 2
    else:
        d = 3

    if handicap >= 2:
        points.add((boardsize - d, 1 + d))
        points.add((1 + d, boardsize - d))

    # Experiments suggest Tygem puts its 3rd handicap stone in the top left

    if handicap >= 3:
        if tygem:
            points.add((1 + d, 1 + d))
        else:
            points.add((boardsize - d, boardsize - d))

    if handicap >= 4:
        if tygem:
            points.add((boardsize - d, boardsize - d))
        else:
            points.add((1 + d, 1 + d))

    if boardsize % 2 == 0:      # No handicap > 4 on even sided boards
        return points

    mid = (boardsize + 1) // 2

    if handicap in [5, 7, 9]:
        points.add((mid, mid))

    if handicap >= 6:
        points.add((1 + d, mid))
        points.add((boardsize - d, mid))

    if handicap >= 8:
        points.add((mid, 1 + d))
        points.add((mid, boardsize - d))

    return points


def get_metadata(strings):
    metadata = dict()

    for s in strings:
        if s.startswith("Black: "):
            metadata["PB"] = s[7:].replace("…", "...")
        if s.startswith("White: "):
            metadata["PW"] = s[7:].replace("…", "...")
        if s.startswith("Komi: "):
            try:
                metadata["KM"] = float(s[6:])
            except:
                pass
        if s.startswith("Handicap Stones: "):
            try:
                metadata["HA"] = int(s[17:])
            except:
                pass
        if s.startswith("Status: "):
            if "Time up. Black loses" in s:
                metadata["RE"] = "W+T"
            if "Time up. White loses" in s:
                metadata["RE"] = "B+T"
            if "Black has resigned" in s:
                metadata["RE"] = "W+R"
            if "White has resigned" in s:
                metadata["RE"] = "B+R"
            if "White wins by" in s:
                try:
                    metadata["RE"] = "W+" + re.search(r'White wins by (.+) points', s).group(1)
                except:
                    pass
            if "Black wins by" in s:
                try:
                    metadata["RE"] = "B+" + re.search(r'Black wins by (.+) points', s).group(1)
                except:
                    pass

        if len(s) == 10 and s[4] == "/" and s[7] == "/":
            try:
                year = int(s[0:4])
                month = int(s[5:7])
                day = int(s[8:10])
                metadata["DT"] = "{:04d}-{:02d}-{:02d}".format(year, month, day)
            except:
                pass

    metadata["GM"] = 1
    metadata["FF"] = 4
    metadata["CA"] = "UTF-8"
    return metadata


def make_sgf_file_from_archive(arch, boardsize, outfilename):
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
        for line in codecs.iterdecode(page, encoding = "utf8", errors = "replace"):
            lines.append(line)

    strings = []

    for line in lines:
        extract = re.search(UNICODE_STRING_REGEX, str(line))
        if extract:
            strings.append(extract.group(1))

    metadata = get_metadata(strings)
    metadata["SZ"] = boardsize

    goodstrings = []

    nextstart = 1
    for s in strings:
        startstring = "{} ".format(nextstart)
        if s.startswith(startstring):
            goodstrings.append(s)
            nextstart += 1

    sgf = "(;"
    colour = "B"

    for key in metadata:
        sgf += key + "[" + str(metadata[key]) + "]"

    if metadata.get("HA"):
        colour = "W"
        points = handicap_points(boardsize, metadata["HA"])
        sgf += "AB"
        for point in points:
            sgf += "[{}]".format(sgf_point_from_point(point[0], point[1]))
        sgf += "C[WARNING: Handicap placement has been guessed at by csa2sgf.py]"

    for s in goodstrings:

        # Example good string: "17 K,1600:00:00102260.5070411.5±16 F,170.001037"
        # Meaning:
        #
        # Move 17, K16 was played, thinking time was 00:00:00, 10226 playouts,
        # Black wins P = 0.507041, projected score = 1.5±16, CrazyStone prefers
        # F17, delta is 0.001037


        # First REGEX

        extract = re.search(MOVE_REGEX, s)
        if extract:

            # i.e. there actually is a move

            actual_move = extract.group(1)
            letter = actual_move[0]
            number = int(actual_move[2:])
            sgf_move = sgf_point_from_english_string("{}{}".format(letter, number), boardsize)

            sgf += ";{}[{}]".format(colour, sgf_move)
            comment = ""

            colour = "B" if colour == "W" else "W"          # This is for the next move after this one

            # Second REGEX

            extract = re.search(OTHER_MOVE_REGEX, s[8:])    # Don't start at start so as not to get the first move
            if extract:
                better_move = extract.group(1)
                letter = better_move[0]
                number = int(better_move[2:])
                sgf_move = sgf_point_from_english_string("{}{}".format(letter, number), boardsize)

                sgf += "TR[{}]".format(sgf_move)

                delta = extract.group(2)

                if better_move != actual_move:
                    comment += "CS prefers {}{}".format(letter, number)
                    try:
                        delta_float = float(delta)
                        comment += " -- delta: {:.2f} %\n".format(delta_float * 100)
                        if delta_float >= HOTSPOT_DELTA:
                            sgf += "HO[1]"
                    except:
                        comment += "\n"

            # Third REGEX

            extract = re.search(SITUATION_REGEX, s)
            if extract:
                situation_float = float(extract.group(1))
                comment += "Black winrate: {:.2f} %\n".format(situation_float * 100)

            # Done

            if comment:
                comment = comment.strip()
                sgf += "C[{}]".format(comment)

    sgf += ")"

    with open(outfilename, "w", encoding="utf8") as outfile:
        outfile.write(sgf)


def main():

    input_filepaths = []
    boardsize = 19

    for n, arg in enumerate(sys.argv):
        if n > 0:
            if sys.argv[n - 1] == "--size":
                try:
                    boardsize = int(arg)
                except:
                    print("Did not understand --size {}".format(arg))
                    sys.exit()
            elif arg != "--size" and sys.argv[n - 1] != "--size":
                input_filepaths.append(arg)

    for zfile in input_filepaths:
        try:
            with zipfile.ZipFile(zfile) as arch:
                try:
                    outfilename = "{}_analysis.sgf".format(zfile)
                    make_sgf_file_from_archive(arch, boardsize, outfilename)
                    print("{} converted to {}".format(zfile, outfilename))
                except:
                    print("Couldn't parse {} at size {}".format(zfile, boardsize))
        except:
            print("Couldn't open {} or interpret it as a zip file".format(zfile))


if __name__ == "__main__":
    main()
