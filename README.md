# cbr2cbz
Python script that converts compressed CBR and CBZ comic archives to stored CBZ

Requires: Python 3.2+, unrar utility
Optional requirements: Imagemagick identify and convert programs for --shrink

Comicrack for Android recommends CBZ archives without compression (the images in archives are typically compressed anyway, so using zip/rar compression doesn't save much space and uses significant memory/power on mobile devices).
cbr2cbz.py will take a source folder of CBR files and convert to CBZ (output goes to a new folder).

For the moment it converts all output file names to ANSI (because unicode scares me, and I'm unsure of security implications of unicode characters).

Currently GNU/Linux, but uses mostly OS agnostic modules so should be relatively easy to convert to Windows.

Requires an unrar utility for unpacking.

Additional optional features include:
* Convert existing CBZ files to uncompressed CBZ
* Copy non CBR/CBZ files
* Flat mode - output all files in the top level of the destination folder
* Pattern matching to decide what files to copy/convert
* Optional aggressive shrinking of page (lossy conversion)
<pre>
usage: cbr2cbz.py [-h] [-c] [-z] [--shrink] [--forceshrink] [-f] [-m MATCH]
                  [-e EXCLUDE] [-i] [-v] [-w]
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
  --forceshrink         [ WARNING - LOSSY ] as --shrink, but attempt on all
                        pages
  -f, --flat            Flat mode - do not create output subdirectories
  -m MATCH, --match MATCH
                        only process paths matching Regular Expression
  -e EXCLUDE, --exclude EXCLUDE
                        exclude source files matching Regular Expression
  -i, --ignorecase      ignore case in RE matching -m
  -v, --verbose         print additional information (multiple accepted eg.
                        -vvv)
  -w, --whatif          test mode - no action


</pre>

