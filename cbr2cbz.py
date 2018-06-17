#!/usr/bin/python
"""
cbr2cbz.py - converts CBR comic book files (RAR) to CBZ (as uncompressed zip)

Requires system commands: unrar, zip
"""
# Usage string used by optparse in main(), but it seems a shame to double up on documentation text

import os
import sys
import re
import shutil
import argparse # argparse requires 3.2 and up
# Subprocess for external unrar command
import subprocess
import zipfile

# Kludgy global for the temp folder (used by all the functions in one way or other)
# New - use /tmp (which is in RAM/Swap tmpfs) for speed and reduced SSD/drive wear
cbr2cbztemp = os.path.abspath(os.path.expanduser("/tmp/cbr2cbztemp-u{0}/p{1}".format(os.getuid(),os.getpid())))

def cbr2cbzclean(create=True,delete=False):
	# Creates (if necessary) and cleans the temporary folder
	if os.path.exists(cbr2cbztemp):
		if os.path.isdir(cbr2cbztemp):
			# Clean any files/folders in temp directory
			for fileob in os.listdir(cbr2cbztemp):
				filename=os.path.join(cbr2cbztemp,fileob)
				if os.path.isfile(filename):
					os.remove(filename)
				elif os.path.isdir(filename):
					shutil.rmtree(filename)
				else:
					exit("ERROR: Don't know how to handle removing '{0}'".format(filename))
			if delete:
			    shutil.rmtree(cbr2cbztemp)
		else:
			exit("Temp directory {0} exists but is not a directory.".format(cbr2cbztemp))
	elif create:
		# temp folder doesn't exist
		print("Creating {0}".format(cbr2cbztemp))
		os.makedirs(cbr2cbztemp)
	else:
	    # Temp directory doesn't exist and we're not creating it
	    return

# Function that takes input and output file names and converts from CBR to CBZ
# Returns True if managed to create .CBZ and False on error
def cbr2cbz(infile, outfile,verbose=0,matchpagelist=[],excludepagelist=[],shrink=False,shrinkKB=300,shrinkQual=40,shrinkHeight=1500,whatif=False):
	if not os.path.isfile(infile):
		print("ERROR - infile doesn't exist")
		return(False)
		
	if os.path.exists(outfile):
		if verbose>0:
			# This shouldn't happen, test is done in main(). Leave old check here anyway
			print ("ERROR: {0} exists.".format(outfile))
		return(False)

	# Clean the temporary folder
	cbr2cbzclean()
			
	# Double check temp is empty
	if len(os.listdir(cbr2cbztemp))!=0:
		exit("ERROR: Temp folder {0} could not be emptied!".format(cbr2cbztemp))
	
	# Changing to temp directory is necessary to keep zip file paths short
	os.chdir(cbr2cbztemp)
	if (os.getcwd() != cbr2cbztemp):
		exit("Could not change to temp directory {0}".format(cbr2cbztemp))
			
	# Output folder should exist (created in main()) but leave check here anyway			
	if not os.path.isdir(os.path.dirname(outfile)):
		os.makedirs(os.path.dirname(outfile))
	
	# New - use is_zipfile. We trust zipfile more than the external unrar
	if zipfile.is_zipfile(infile):
		# Now using zipfile - precondition: is_zipfile() is True
		if verbose>1:
			print ("** Unzipping {0}".format(infile))
		try:
			myzip=zipfile.ZipFile(infile,mode='r')
			# End of unziping try
		except:
			print("Zipfile unpack error: {0}".format(sys.exc_info()[0]))
			return(False)
			# End of unziping except
		try:
			listinf=myzip.infolist()
		except:
			print("ERROR: Zipfile list error: {0}".format(sys.exc_info()[0]))
			return(False)			
		# Extract contents - .extract() has path safety checks, extractall() does not
		for zi in listinf:
			if verbose > 2:
				print("*** Extract: {0}".format(zi.filename))
			try:
				myzip.extract(zi) 
			except:
				print("ERROR: Zip extracting: {0} - {1}".format(infile,sys.exc_info()[0]))
				myzip.close()
				return(False)
		myzip.close()
		# End of if is_zipfile() unzip
	else:
		# Assume it's a RAR and launch subprocess unrar
		if verbose>1:
			print ("** unrar {0}".format(infile))
		subcom=["unrar", "x", infile, cbr2cbztemp]
		if verbose>3:
			print ("** {0}".format(subcom))
		try:
			output=subprocess.check_output(subcom)
		except subprocess.CalledProcessError as e:
			output=e.output
			# Erroring here means that the file wasn't a zip. Couldn't unpack 
			print("ERROR: CalledProcessError: unrar {0}".format(infile))
			if verbose > 0:
				try:
					output=output.decode("UTF-8","ignore")
				except:
					print(format(sys.exc_info()[0]))
				print ("* {0}".format(output))
			return(False) # Failed via unrar subprocess error
		except:
			print(format(sys.exc_info()[0]))
			print("No process output available")
			return(False) # Failed via unrar misc error
		# No exception on subprocess, try to display output
		if verbose > 2:
			try:
				output=output.decode("UTF-8","ignore")
			except:
				print(format(sys.exc_info()[0]))
			print ("*** {0}".format(output))			
		# End if is_zipfile() unrar method
	
	# Check what files need to be excluded
	for root,dirs,files in os.walk(cbr2cbztemp):
		dirs.sort()
		files.sort()
		for leaf in files:	
			if matchpagelist:
				epf = True # exclude page flag
				for m in matchpagelist:
					# leaf for now, consider using folder as well
					if re.search(m,leaf)!=None:
						epf=False
						break
			else:
				epf=False
			
			if excludepagelist and not epf:
				for m in excludepagelist:
					# leaf for now, consider using folder as well
					if re.search(m,leaf)!=None:
						epf=True
						break
			if epf:
				if verbose>2:
					print("*** Excluding page: {0}".format(leaf))
				os.unlink(os.path.join(root,leaf))	
				continue
	
	# Shrink archive
	if shrink:
		if verbose>1:
			print("** Shrinking {0}".format(infile))
		# Walk through the extracted files
		for root,dirs,files in os.walk(cbr2cbztemp):
			dirs.sort()
			files.sort()
			for leaf in files:
				if verbose>3:
					print ("*** Assessing {0}".format(leaf))
				shrinkfile=os.path.join(root,leaf)
				# Use Imagemagick identify to get size, extension, type, width and height
				subcom=["identify", "-precision", "16", "-format", '%b %e %m %W %H', "-quiet", shrinkfile]
				if verbose>4:
					print ("***** {0}".format(subcom))
				try:
					output=subprocess.check_output(subcom)
				except subprocess.CalledProcessError as e:
					output=e.output
					if verbose>3:
						print("**** ERROR: CalledProcessError: identify {0}".format(leaf))
						try:
							output=output.decode("UTF-8","ignore")
							print ("**** {0}".format(output))
						except:
							print(format(sys.exc_info()[0]))
					continue
				except:
					if verbose>3:
						print("**** ERROR: Could not get image information on {0}".format(leaf))
					continue
				
				# Extract image stats
				try:
					output=output.decode("UTF-8","ignore")
					(imgsize,imgext,imgtype,imgx,imgy)=output.split(" ")
					imgsize=int(imgsize.replace("B",""))
					imgx=int(imgx)
					imgy=int(imgy)
					# imgar is the aspect ratio
					imgar=imgx/imgy
					if verbose>4:
						print("***** Imagestats:",imgsize,imgext,imgtype,imgx,imgy,imgar)
				except:
					if verbose>3:
						print("**** Output: {0}".format(output))
						print(format(sys.exc_info()[0]))
						print("**** ERROR: Could not extract image sizes")
					continue
				
				# Only process understood file types
				if not (imgtype=='JPEG' or imgtype=='PNG'):
					continue
					 
				# Check for a name clash
				# This would happen with archive files which only differ by extension
				# eg. file1.png, file1.jpg - when file1.png is shrunk
				if imgext!='jpg' and os.path.exists(shrinkfile.replace(imgext,"jpg")):
					if verbose>0:
						print("* WARNING: Shrink filename clash: {0} -> {1}",shrinkfile, leaf.replace(imgext,"jpg"))
					continue # Don't attempt shrinking this file as we can't rename it
				
				# We expect wider pages to be larger so our allowance is based on the aspect ratio (imgar)
				# Shrink limit is shrinkKB * 1000 * 1.5 * imgar. AR is typically about .65 for single pages - hence 1.5 multiplier
				# If a page is less than shrinklimit skip shrink attempt (to save time and image quality)
				shrinklimit=(imgar*1.5*shrinkKB*1000)
				if imgsize>shrinklimit:
					subcom=["convert",shrinkfile,"-quality", str(shrinkQual), "-resize", "x"+str(shrinkHeight)+">",shrinkfile+".shrink.jpg"]
					if verbose>4:
						print ("***** {0}".format(subcom))
					try:
						# Call convert
						output=subprocess.check_output(subcom)
					except subprocess.CalledProcessError as e:
						output=e.output
						if verbose>4:
							print("***** ERROR: CalledProcessError: convert {0}".format(shrinkfile))
							try:
								output=output.decode("UTF-8","ignore")
							except:
								print(format(sys.exc_info()[0]))
							print ("* {0}".format(output))
						if os.path.exists(shrinkfile+".shrink.jpg"):
							try:
								os.unlink(shrinkfile+".shrink.jpg")
								continue
							except:
								if verbose>0:
									print("* Could not clean up shrink file {0}".format(shrinkfile+".shrink.jpg"))
								return(False)
					except:
						if verbose>4:
							print(format(sys.exc_info()[0]))
							print("ERROR: Could not convert file {0}".format(shrinkfile))
						if os.path.exists(shrinkfile+".shrink.jpg"):
							try:
								os.unlink(shrinkfile+".shrink.jpg")
								continue
							except:
								if verbose>0:
									print("* Could not clean up shrink file {0}".format(shrinkfile+".shrink.jpg"))
								return(False)
							
					# Do a check the new file is smaller before replacing
					oldsize=os.stat(shrinkfile).st_size
					newsize=os.stat(shrinkfile+".shrink.jpg").st_size
					if (oldsize*0.9)>newsize:
						os.unlink(shrinkfile) # Not necessary on POSIX
						if imgext=="":
							newname=shrinkfile+".jpg"
						else:
							newname=re.sub("\."+re.escape(imgext)+"$",".jpg",shrinkfile)
						os.rename(shrinkfile+".shrink.jpg",newname)
						if verbose>2:
							print("*** Shrank    {3} {1}/{2} : {0}".format(leaf, newsize, oldsize, round(newsize/oldsize,2)))
					else:
						if verbose>2:
							print("*** No shrink {3} {1}/{2} : {0}".format(leaf, newsize, oldsize, round(newsize/oldsize,2)))
						os.unlink(shrinkfile+".shrink.jpg")
					
	# Collate a list of all files and force sort order into zip
	zipfiles=[] #os.listdir(cbr2cbztemp)
	for root,dirs,files in os.walk(cbr2cbztemp):
		dirs.sort()
		files.sort()		
		if verbose>2:
			print("*** Adding zip directory : {0} - files:{1} ".format(root,len(files)))
		for leaf in files:
			addfile=os.path.join(root,leaf)
			zipfiles.append(addfile.replace(cbr2cbztemp+'/',''))
			if verbose>3:
				print("**** Adding zip list file : {0}".format(leaf))		
	zipfiles.sort() # To be sure, test 

	# Compress a new cbz using zipfile
	if verbose>1:
		print ("** Creating with zipfile: {0}".format(outfile))
	try:
		outzip=zipfile.ZipFile(outfile,mode='x',compression=zipfile.ZIP_STORED)

	except FileExistsError:
		# This really shouldn't happen, tested in main() and earlier in this function
		print ("ERROR: File exists: {0}".format(outfile))
		return(False)
	except NameError as e:
		print("ERROR: Zipfile creation NameError")
		print(e)
		return(False)
	except:
		print("ERROR: Zipfile creation error")
		print(sys.exc_info()[0])
		return(False)

	for zf in zipfiles:
		# Force filenames to be ascii and add to zip
		try: 
			zfarcname=zf
			zfarcname=zfarcname.replace(u'\xa0', ' ')
			zfarcname=zfarcname.encode('ascii', 'replace').decode('ascii', 'replace')
			outzip.write(zf,arcname=zfarcname)
			#outzip.write(zf)
			if verbose>2:
				print("*** Adding: {0}".format(zf))
		except:
			print("Error adding file:{0}".format(zf))
			print(sys.exc_info()[0])
			outzip.close()
			os.remove(outfile)
			return(False)
	outzip.close()
	return(True)	
	# Earlier steps should have returned... bug
	print("ERROR: default return reached in cbr2cbz()")
	return(False)
				
def main():
	description="Converts, copies or shrinks CBR/CBZ archives to stored CBZ"
	epilog="""
Pattern matching options (-m, -e, --pageexclude) may be used more than once to match against multiple Regular Expressions.

To see examples use "--examples a b" (removing dummy source/destination requirement is a work in progress)
"""
	examples="""
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

"""
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description=description,epilog=epilog)
	#parser.usage=usage
	parser.add_argument("--examples",default=False,action="store_true",help="view this help with additional examples (requires dummy source/destination arguments)")
	parser.add_argument("-c","--copy",default=False,action="store_true", dest="copy",help="copy non CBR files to destination")
	parser.add_argument("--noconvert",default=False,action="store_true", help="copy CBR/CBZ instead of converting (implies -c)")
	parser.add_argument("-z","--zipforce",default=False,action="store_true", dest="zipforce",help="re-zip CBZ archives (remove wasteful compression)")
	parser.add_argument("--shrink",default=False,action="store_true", dest="shrink",help="[ WARNING - LOSSY ] aggressively shrink large page files with JPEG")
	parser.add_argument("--shrinkKB",default=300, type=int,action="store",help="with --shrink process pages larger than this many KB (default = 300)")
	parser.add_argument("--shrinkQual",default=40, type=int,action="store",help="with --shrink use custom JPEG quality (default = 40)")
	parser.add_argument("--shrinkHeight",default=1500, type=int,action="store",help="with --shrink sets maximum pixel height of page (default = 1500)")
	parser.add_argument("-f","--flat",default=False,action="store_true", dest="flat",help="Flat mode - do not create output subdirectories")
	parser.add_argument("-m","--match",default=[],action="append", dest="match",help="only process paths matching Regular Expression")
	parser.add_argument("--matchfile",default=False,action="store", help="process source files matching RE in file")
	parser.add_argument("-e","--exclude",default=[],action="append", dest="exclude",help="exclude source files matching Regular Expression")
	parser.add_argument("--excludefile",default=False,action="store", help="exclude source files matching RE in file")
	parser.add_argument("--matchpage",default=[],action="append", dest="matchpage",help="include only page matching Regular Expression")
	parser.add_argument("--matchpagefile",default=False,action="store", help="include pages matching RE in file")
	parser.add_argument("--excludepage",default=[],action="append", dest="excludepage",help="exclude page matching Regular Expression")
	parser.add_argument("--excludepagefile",default=False,action="store", help="exclude pages matching RE in file")
	parser.add_argument("--cs","--case-sensitive",default=False,action="store_true", dest="cs",help="use case sensitive RE matching")
	parser.add_argument("-v","--verbose",default=0,action="count", dest="verbose",help="print additional information (multiple accepted eg. -vvv)")
	parser.add_argument("-w","--whatif",default=False,action="store_true", dest="whatif",help="test mode - no action")
	parser.add_argument('source',default=False,help="source file or directory")
	parser.add_argument('dest',default=False, help="destination directory")
	options = parser.parse_args()
		
	if options.verbose>1:
		print ("** Options:",str(options))
	
	if options.examples:
		parser.print_help()
		print(examples)
		exit()
	
	if options.whatif:
		print("Running in test (WHATIF) mode")
	
	# Set the extensions we're looking for for conversion
	if options.zipforce:
		CBxMatch='\.[Cc][bB][rRzZ]$'
	else:
		CBxMatch='\.[Cc][bB][rR]$'
	
	if options.noconvert:
		options.copy=True
		
	# Construct lists of RE matches for match, exclude, excludepage
	if options.cs:
		reflags= 0
	else:
		reflags= re.I
		'''
	if options.match:
		matchlist = [re.compile(x.rstrip(),reflags) for x in options.match]
	else:
		matchlist=[]
		'''
	matchlist=[]
	if options.matchfile:
		try:
			f=os.path.abspath(os.path.expanduser(options.matchfile))
			text_file = open(f, "r")
			matchlist = matchlist + [re.compile(x.rstrip(),reflags) for x in text_file.readlines()]
			text_file.close()
		except:
			exit("Error loading match page file")
	if options.match:
		matchlist = matchlist + [re.compile(x.rstrip(),reflags) for x in options.match]
		'''
	if options.exclude:
		excludelist = [re.compile(x.rstrip(),reflags) for x in options.exclude]
	else:
		excludelist=[]
'''
	excludelist=[]
	if options.excludefile:
		try:
			f=os.path.abspath(os.path.expanduser(options.excludefile))
			text_file = open(f, "r")
			excludelist = excludelist + [re.compile(x.rstrip(),reflags) for x in text_file.readlines()]
			text_file.close()
		except:
			exit("Error loading exclude page file")
	if options.exclude:
		excludelist = excludelist + [re.compile(x.rstrip(),reflags) for x in options.exclude]

	matchpagelist=[]
	if options.matchpagefile:
		try:
			f=os.path.abspath(os.path.expanduser(options.matchpagefile))
			text_file = open(f, "r")
			matchpagelist = matchpagelist + [re.compile(x.rstrip(),reflags) for x in text_file.readlines()]
			text_file.close()
		except:
			exit("Error loading match page file")
	if options.matchpage:
		matchpagelist = matchpagelist + [re.compile(x.rstrip(),reflags) for x in options.matchpage]

	excludepagelist=[]
	if options.excludepagefile:
		try:
			f=os.path.abspath(os.path.expanduser(options.excludepagefile))
			text_file = open(f, "r")
			excludepagelist = excludepagelist + [re.compile(x.rstrip(),reflags) for x in text_file.readlines()]
			text_file.close()
		except:
			exit("Error loading exclude page file")
		
	if options.excludepage:
		excludepagelist = excludepagelist + [re.compile(x.rstrip(),reflags) for x in options.excludepage]

	if options.verbose>3:
		print ("**** Options:",str(options))
		print("**** matchlist:",matchlist)
		print("**** excludelist:",excludelist)
		print("**** matchpagelist:",matchpagelist)
		print("**** excludepagelist:",excludepagelist)
		
	source= os.path.abspath(os.path.expanduser(options.source))
	dest= os.path.abspath(os.path.expanduser(options.dest))

	if source == dest:
		exit("Source = dest {0}".format(source))
		
	if not os.path.exists(source):
		exit("Error: Source '{0}' does not exist.".format(source))
			
	if os.path.isfile(source):
		# Change around options to handle single file
		#singlefilematch="^{0}$".format(re.escape(source))
		# New way - forcing file/dir walk to just be the one file
		singlefile=os.path.basename(source)
		options.copy=True
		source=os.path.dirname(source)
		if options.verbose>1:
			print("** Switching from filemode to dirmode")
			print("** Source: {0}".format(source))
			#print("** Dest: {0}".format(dest))
	else:
		#singlefilematch=False
		singlefile=False
	
	if not os.path.isdir(source):
		exit("Error: Source '{0}' is not a file or folder.".format(source))
	
	rescount={x:0 for x in ["copy","convert","excluded","failed","skipped"]}
	
	if options.verbose>1:
		print ("** Process source directory : "+source)
		
	outdir=dest # Default used by FLAT MODE
	
	# recurse with os.walk()
	failedlist=[]
	
	for root,dirs,files in os.walk(source):
		
		# A bit kludgey, but restrict dirs and files to the single file for SFM
		if singlefile:
			del dirs[:]
			files=[singlefile]
		
		dirs.sort()
		files.sort()
		
		if re.match(re.escape(dest),root):
			# Current source dir is under the destination - this could be BAD
			if options.verbose>1:
				print("** Skipping dir - inside destination: {0}".format(root))
			continue
		
		if options.verbose>1:
			print("** Directory : {0} - subdirs:{1} files:{2} ".format(root,len(dirs),len(files)))
		
		if len(files)>0:
			if not options.flat:
				outdir=root.replace(source,dest)
				outdir=outdir.replace(u'\xa0', ' ')
				outdir=outdir.encode('ascii', 'replace').decode('ascii', 'replace')
		else:
			continue
		
		for leaf in files:
			infile= os.path.join(root,leaf)
			
			if options.verbose>2:
				print ("*** File: {0}".format(leaf))
				
			# Check for match/exclude setting matchflag
			if matchlist :
				matchflag=False
				for m in matchlist:
					if re.search(m,infile)!=None:
						matchflag=True
						break
			else:
				matchflag=True
				
			if excludelist and matchflag:
				for m in excludelist:
					if re.search(m,infile)!=None:
						matchflag=False
						break
			
			if options.verbose > 4:
				print("***** Matchflag: {0}".format(matchflag))
					
			if not matchflag:
				# Excluded 
				if options.verbose>0:
					print("* ResultExcluded: {0}".format(infile))
				rescount["excluded"] += 1
				continue
			
			if options.noconvert:
				convertflag=False
			else:
				# Check file extension to decide if we're converting or proceeding to copy
				convertflag=re.search(CBxMatch,leaf)
				
			if not(convertflag or options.copy):
				continue
			
			if not os.path.isdir(outdir):
				if options.whatif:
					print("WHATIF: Create directory {0}".format(outdir))
				else:
					if options.verbose>2:
						print ("**   Creating directory {0}".format(outdir))
					os.makedirs(outdir)

			outfile=os.path.join(outdir,leaf)
			outfile=outfile.replace(u'\xa0', ' ')
			outfile=outfile.encode('ascii', 'replace').decode('ascii', 'replace')
			if convertflag:
				outfile=re.sub('\.[Cc][bB][rR]$','.cbz',outfile)

			if os.path.exists(outfile):
				rescount["skipped"] += 1
				if options.verbose>0:
					print("* ResultSkipped: {0}".format(infile))
				continue
			
			if convertflag:
				if options.whatif:
					print("WHATIF: Convert CBx >cbr2cbz({0},{1})".format(infile,outfile))
				else:
					if options.verbose>0:
						print ("* Converting {0}".format(infile))
					if(cbr2cbz(infile,outfile,verbose=options.verbose,matchpagelist=matchpagelist,excludepagelist=excludepagelist,shrink=options.shrink,shrinkKB=options.shrinkKB,shrinkQual=options.shrinkQual,shrinkHeight=options.shrinkHeight,whatif=options.whatif)):
						rescount['convert'] += 1
						if options.verbose>0:
							oldsize=os.stat(infile).st_size
							newsize=os.stat(outfile).st_size
							print("* ResultConvert: {0} {1}/{2} MB {3}".format(round(newsize/oldsize,3),round(newsize/1000000,1),round(oldsize/1000000,1),infile))
					else:
						rescount['failed'] += 1
						if options.verbose>0:
							print("* ResultFailed: {0}".format(infile))
						failedlist.append(infile)
				continue
				
			# not convertflag so options.copy is set
			if options.verbose>2:
				print ("***   No CBx extension detected, copy option set")
			if options.whatif:
				print ("WHATIF: Copy to {0} : {1}".format(outdir,leaf))
			else:
				if options.verbose>0:
					print ("* Copying {0}".format(os.path.join(root,leaf)))
				shutil.copyfile(os.path.join(root,leaf),os.path.join(outdir,leaf))
				rescount['copy'] += 1
				if options.verbose>0:
					print("* ResultCopied: {0}".format(infile))

	# Clean out the temporary folder
	cbr2cbzclean(create=False,delete=True)
	if options.verbose>0:
		print("* Results:",rescount)
		for countkey in rescount.keys():
			print("*  {0}: {1}".format(countkey,rescount[countkey]))
	if options.verbose>1:
		print("** Failed conversions:")
		for failedfile in failedlist:
			print(failedfile)
	
main()
