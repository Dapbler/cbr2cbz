# cbr2cbz
Python script that converts compressed CBR and CBZ comic archives to stored CBZ

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
<pre>
Usage: 
 Use 1 - single file:      cbr2cbz.py [options] source_file destination_dir
 Use 2 - folder contents:  cbr2cbz.py [options] source_dir destination_dir

By default only *.CBR (case insensitive) are processed into CBZ. CBZ may optionally be repacked.
With -c (copy) mode other files will be copied.
Output format for CBR to CBZ conversion is uncompressed zip (recommended for ComicRack on Android)

Options:
  -h, --help            show this help message and exit
  -c, --copy            copy non CBR files to destination
  -z, --zipforce        re-zip CBZ archives (remove wasteful compression)
  -f, --flat            Flat mode - do not create output subdirectories
  -m MATCH, --match=MATCH
                        only process paths matching Regular Expression
  -e, --exclude         invert RE matching - exclude matches
  -i, --ignorecase      ignore case in RE matching -m
  -v, --verbose         print additional information (multiple accepted eg.
                        -vvv)
  -w, --whatif          test mode - no action
</pre>

