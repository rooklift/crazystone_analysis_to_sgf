# crazystone_analysis_to_sgf
Convert a CrazyStone OXPS analysis file to SGF

To use:

* In CrazyStone, use the Print option to produce an OXPS file of the analysis (XPS may work also)
* Open that file with the script (i.e. send the script an argument to the filepath)
* If all goes well, the SGF will appear

Limitations:

* Assumes 19x19
* The location of handicap stones has to be guessed: free handicaps will be placed wrong, and handicap 3 is dubious
