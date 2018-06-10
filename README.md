# cbr2cbz
Python script that converts compressed CBR and CBZ comic archives to stored CBZ

Requires: Python 3.2+, unrar utility

Optional requirements: Imagemagick identify and convert programs for --shrink

Comicrack for Android recommends CBZ archives without compression (the images in archives are typically compressed anyway, so using zip/rar compression doesn't save much space and uses significant memory/power on mobile devices).
cbr2cbz.py will take a source folder of CBR files and convert to CBZ (output goes to a new folder).

Note: Output file names are converted to ANSI. Let me know if you need unicode support.

https://github.com/Dapbler/cbr2cbz

Currently GNU/Linux, but uses mostly OS agnostic modules so should be relatively easy to convert to Windows (subprocess commands will need modification).

Additional optional features include:
* Convert existing CBZ files to uncompressed CBZ
* Copy non CBR/CBZ files
* Flat mode - output all files in the top level of the destination folder
* Pattern matching to decide what files to copy/convert (multiple pattern optons may be set and all are checked)
* Exclude archived page names matching regular expressions (from file or command line)
* Shrinking of page (lossy conversion) for non-archival use on devices with limited storage/memory
* Shrinking heuristics and compression settings now exposed via --shrinkXXXX settings

<pre>
Usage: cbr2cbz.py [-h] [-c] [-z] [--shrink] [--shrinkKB SHRINKKB]
                  [--shrinkQual SHRINKQUAL] [--shrinkHeight SHRINKHEIGHT] [-f]
                  [-m MATCH] [-e EXCLUDE] [--excludepage EXCLUDEPAGE]
                  [--excludepagefile EXCLUDEPAGEFILE] [--cs] [-v] [-w]
                  source dest

Converts CBR archives to CBZ

positional arguments:
  source                source file or directory
  dest                  destination directory

optional arguments:
  -h, --help            show this help message and exit
  -c, --copy            copy non CBR files to destination
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
  --excludepage EXCLUDEPAGE
                        exclude page matching Regular Expression
  --excludepagefile EXCLUDEPAGEFILE
                        exclude pages matching RE in file
  --cs, --case-sensitive
                        use case sensitive RE matching -m
  -v, --verbose         print additional information (multiple accepted eg.
                        -vvv)
  -w, --whatif          test mode - no action

</pre>

