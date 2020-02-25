# cbr2cbz

Python script that converts compressed CBR and CBZ comic archives to stored CBZ

**Requires:** Python 3.2+, unrar utility

**Optional requirements:** Imagemagick identify and convert programs for --shrink

**OS:** Linux (and probably Mac OS X).

Bug with an issue if you want Windows and want to do some testing.

## Description

To reduce decompression space and power requirements ComicRack for Android
recommends CBZ archives without compression.

Images in archives are typically compressed, so using zip/rar compression
saves as little as 1-2%.

cbr2cbz will take a source folder of CBR files and convert to CBZ
(output goes to a new folder).

Note: Output file names are converted to ANSI. Let me know if you need unicode
support on the [Github page]: https://github.com/Dapbler/cbr2cbz

Currently GNU/Linux, but uses mostly OS agnostic modules so should be
relatively easy to convert to Windows (subprocess commands will need modification).

Additional optional features include:

* Convert existing CBZ files to uncompressed CBZ
* Copy non CBR/CBZ files
* Flat mode - output all files in the top level of the destination folder
* Pattern matching to decide what files to copy/convert (multiple pattern optons may be set and all are checked)
* Including/exclude archived page names matching regular expressions (eg. include pages 001-009 for a test sample)
* Shrinking of page (lossy conversion) for non-archival use on devices with limited storage/memory (often reducing size by 85%)
* Shrinking heuristics and compression settings now exposed via --shrinkXXXX settings

<pre>
usage: cbr2cbz.py [-h] [--examples] [-c] [--noconvert] [-z] [--shrink]
                  [--shrinkKB SHRINKKB] [--shrinkQual SHRINKQUAL]
                  [--shrinkHeight SHRINKHEIGHT] [-f] [-m MATCH] [-e EXCLUDE]
                  [--matchpage MATCHPAGE] [--matchpagefile MATCHPAGEFILE]
                  [--excludepage EXCLUDEPAGE]
                  [--excludepagefile EXCLUDEPAGEFILE] [--cs] [-v] [-w]
                  source dest

Converts, copies or shrinks CBR/CBZ archives to stored CBZ

positional arguments:
  source                source file or directory
  dest                  destination directory

optional arguments:
  -h, --help            show this help message and exit
  --examples            view this help with additional examples (requires
                        dummy source/destination arguments)
  -c, --copy            copy non CBR files to destination
  --noconvert           copy CBR/CBZ instead of converting (implies -c)
  -z, --zipforce        re-zip CBZ archives (remove wasteful compression)
  --shrink              [ WARNING - LOSSY ] aggressively shrink large page
                        files with JPEG
  --shrinkKB SHRINKKB   with --shrink process pages larger than this many KB
                        (default = 300)
  --shrinkQual SHRINKQUAL
                        with --shrink use custom JPEG quality (default = 40)
  --shrinkHeight SHRINKHEIGHT
                        with --shrink sets maximum pixel height of page
                        (default = 1500)
  -f, --flat            Flat mode - do not create output subdirectories
  -m MATCH, --match MATCH
                        only process paths matching Regular Expression
  -e EXCLUDE, --exclude EXCLUDE
                        exclude source files matching Regular Expression
  --matchpage MATCHPAGE
                        include only page matching Regular Expression
  --matchpagefile MATCHPAGEFILE
                        include pages matching RE in file
  --excludepage EXCLUDEPAGE
                        exclude page matching Regular Expression
  --excludepagefile EXCLUDEPAGEFILE
                        exclude pages matching RE in file
  --cs, --case-sensitive
                        use case sensitive RE matching
  -v, --verbose         print additional information (multiple accepted eg.
                        -vvv)
  -w, --whatif          test mode - no action
  --imversion IMVERSION
                        set ImageMagick version command format (default = 6)
  --tempdir TEMPDIR     use TEMPDIR as temporary file directory


Pattern matching options (-m, -e, --pageexclude) may be used more than once to match against multiple Regular Expressions.

To see examples use "--examples a b" (removing dummy source/destination requirement is a work in progress)

Examples:

Convert all *.CBR files in directory CBR/ to CBZ format and put the output in /tmp/test
    cbr2cbz.py CBR/ /tmp/test/

Convert CBR and CBZ files in CBR to CBZ format:
    cbr2cbz.py -z CBR/ /tmp/test/

Copy files in CBR/, converting CBR files:
    cbr2cbz.py -c CBR/ /tmp/test/

Copy all Cat Conversation files to /tmp/test, without creating subdirectories
    cbr2cbz.py --noconvert -f -m "Cat.*Conv" CBR/ /tmp/test

Copy all files to /tmp/test, excluding Thumbs.db
    cbr2cbz.py --noconvert -e "Thumbs.db" CBR/ /tmp/test

Convert CBR and CBZ files to low quality format and place in CatConv
    cbr2cbz.py -z --shrink CBR/ CatConv/

Convert CBR and CBZ files to extremely low quality format and place in CatConv
    cbr2cbz.py -z --shrink --shrinkKB 100 --shrinkQual 10 CBR/ CatConv/
</pre>