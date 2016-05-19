# crazystone_analysis_to_sgf
Convert a CrazyStone OXPS analysis file to SGF

To use:

* In CrazyStone, use the Print option to produce an OXPS file of the analysis (XPS may work also)
* Open that file with the script (i.e. send the script an argument to the filepath)
* If all goes well, the SGF will appear

Features:

* CrazyStone's favourite move is shown as a triangle.
* Various information is displayed in the comments.
* Moves that CrazyStone thought were particularly bad are flagged with a hotspot property. Some SGF editors such as [Sabaki](https://github.com/yishn/Sabaki) allow you to easily find these (press F2 in Sabaki).

Limitations:

* Assumes 19x19
* The location of handicap stones has to be guessed: free handicaps will be placed wrong, and handicap 3 is dubious
