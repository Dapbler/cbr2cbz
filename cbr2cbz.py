#!/usr/bin/python
"""
cbr2cbz.py - converts CBR comic book files (RAR) to CBZ (as uncompressed zip)

Requires system commands: unrar, zip
"""
# Usage string used by optparse in main(), but it seems a shame to double up on documentation text
usage = """
 Use 1 - single file:      %(prog) [options] <source file> <output directory>
 Use 2 - folder contents:  %(prog) [options] <source directory> <output directory>

By default only *.CBR (case insensitive) are processed into CBZ. CBZ may optionally be repacked.
With -c (copy) mode other files will be copied.
Output format for CBR to CBZ conversion is uncompressed zip (recommended for ComicRack on Android)"""
description="Converts CBR archives to CBZ"
import os
import sys
import re
import shutil
# argparse requires 3.2 and up
import argparse
#from optparse import OptionParser
# Subprocess for external unrar command
import subprocess
import zipfile

# Kludgy global for the temp folder (used by all the functions in one way or other)
# New - use /tmp (which is in RAM/Swap tmpfs) for speed and reduced SSD/drive wear
cbr2cbztemp = os.path.abspath(os.path.expanduser("/tmp/cbr2cbztemp-u{0}/p{1}".format(os.getuid(),os.getpid())))

def cbr2cbzclean():
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
		else:
			exit("Temp directory {0} exists but is not a directory.".format(cbr2cbztemp))
	else:
		# temp folder doesn't exist
		print("Creating {0}".format(cbr2cbztemp))
		os.makedirs(cbr2cbztemp)

# Function that takes input and output file names and converts from CBR to CBZ
# Returns True if managed to create .CBZ and False on error
def cbr2cbz(infile, outfile,verbose=0,shrink=False,forceshrink=False,whatif=False):
	if not os.path.isfile(infile):
		print("ERROR - infile doesn't exist")
		return(False)
		
	if os.path.exists(outfile):
		if verbose>0:
			# This shouldn't happen, test is done in main(). Leave old check here anyway
			print ("ERROR: {0} exists.".format(infile))
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
		#subcom=["unrar", "x",infile.replace('"','\\"'),cbr2cbztemp.replace('"','\\"')]
		if verbose>1:
			print ("** unrar {0}".format(infile))
		subcom=["unrar", "x", infile, cbr2cbztemp]
		if verbose>3:
			print ("** {0}".format(subcom))
		try:
			output=subprocess.check_output(subcom)
		except subprocess.CalledProcessError as e:
			output=e.output
			# Erroring here means that the file couldn't be unzipped either 
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
			
	if shrink or forceshrink:
		for root,dirs,files in os.walk(cbr2cbztemp):
			if verbose>3:
				print("**** Adding zip directory : {0} - files:{1} ".format(root,len(files)))
			if len(files) > 0:
				for leaf in files:
					shrinkfile=os.path.join(root,leaf)
					subcom=["identify", "-precision", "16", "-format", '%b %e %m %W %H', shrinkfile]
					if verbose>3:
						print ("** {0}".format(subcom))
					try:
						output=subprocess.check_output(subcom)
					except subprocess.CalledProcessError as e:
						output=e.output
						print("ERROR: CalledProcessError: identify {0}".format(infile))
						if verbose > 0:
							try:
								output=output.decode("UTF-8","ignore")
							except:
								print(format(sys.exc_info()[0]))
							print ("* {0}".format(output))
						continue
					except:
						print("ERROR: Could not get image information on {0}".format(shrinkfile))
						continue
					
					# Extract image stats
					try:
						output=output.decode("UTF-8","ignore")
						(imgsize,imgext,imgtype,imgx,imgy)=output.split(" ")
						imgsize=int(imgsize.replace("B",""))
						imgx=int(imgx)
						imgy=int(imgy)
						imgar=imgx/imgy
						if verbose>3:
							print("Imagestats:",imgsize,imgext,imgtype,imgx,imgy,imgar)
					except:
						print("Output: {0}".format(output))
						print(format(sys.exc_info()[0]))
						print("ERROR: Could not extract image sizes")
						continue
					
					if ((imgtype=='JPEG' or imgtype=='PNG') and imgsize>(imgar*600000)) or forceshrink:
						subcom=["convert",shrinkfile,"-quality", '40', "-resize", "x1500>",shrinkfile+".shrink.jpg"]
						if verbose>3:
							print ("** {0}".format(subcom))
						try:
							output=subprocess.check_output(subcom)
						except subprocess.CalledProcessError as e:
							output=e.output
							print("ERROR: CalledProcessError: convert {0}".format(shrinkfile))
							if verbose > 0:
								try:
									output=output.decode("UTF-8","ignore")
								except:
									print(format(sys.exc_info()[0]))
								print ("* {0}".format(output))
							try:
								os.unlink(shrinkfile+".shrink.jpg")
							except:
								if verbose>3:
									print("No converted file to clean up")
							continue
						except:
							print(format(sys.exc_info()[0]))
							print("ERROR: Could not convert file {0}".format(shrinkfile))
							try:
								os.unlink(shrinkfile+".shrink.jpg")
							except:
								if verbose>3:
									print("No converted file to clean up")
							continue
						# Do a check the new file is smaller!
						if os.stat(shrinkfile).st_size > os.stat(shrinkfile+".shrink.jpg").st_size:
							os.unlink(shrinkfile)
							os.rename(shrinkfile+".shrink.jpg",shrinkfile.replace(imgext,"jpg"))
						else:
							os.unlink(shrinkfile+".shrink.jpg")
						
	# Collate a list of all files and force sort order into zip
	zipfiles=[] #os.listdir(cbr2cbztemp)
	for root,dirs,files in os.walk(cbr2cbztemp):
		if verbose>3:
			print("**** Adding zip directory : {0} - files:{1} ".format(root,len(files)))
		if len(files) > 0:
			for leaf in files:
				addfile=os.path.join(root,leaf)
				zipfiles.append(addfile.replace(cbr2cbztemp+'/',''))			
	zipfiles.sort()

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

	parser = argparse.ArgumentParser(description=description)
	#parser.usage=usage
	parser.add_argument("-c","--copy",default=False,action="store_true", dest="copy",help="copy non CBR files to destination")
	parser.add_argument("-z","--zipforce",default=False,action="store_true", dest="zipforce",help="re-zip CBZ archives (remove wasteful compression)")
	parser.add_argument("--shrink",default=False,action="store_true", dest="shrink",help="[ WARNING - LOSSY ] recode large page files with JPEG")
	parser.add_argument("--forceshrink",default=False,action="store_true", dest="forceshrink",help="[ WARNING - LOSSY ] as --shrink, but attempt on all pages")
	parser.add_argument("-f","--flat",default=False,action="store_true", dest="flat",help="Flat mode - do not create output subdirectories")
	parser.add_argument("-m","--match",default=[],action="append", dest="match",help="only process paths matching Regular Expression")
	parser.add_argument("-e","--exclude",default=[],action="append", dest="exclude",help="exclude source files matching Regular Expression")
	parser.add_argument("-i","--ignorecase",default=False,action="store_true", dest="ignorecase",help="ignore case in RE matching -m")
	parser.add_argument("-v","--verbose",default=0,action="count", dest="verbose",help="print additional information (multiple accepted eg. -vvv)")
	parser.add_argument("-w","--whatif",default=False,action="store_true", dest="whatif",help="test mode - no action")
	parser.add_argument('source',help="source file or directory")
	parser.add_argument('dest',help="destination directory")
	options = parser.parse_args()
		
	if options.verbose>1:
		print ("** Options:",str(options))
		#print("** Arguments", args)
			
	if options.whatif:
		print("Running in test (WHATIF) mode")
	
	# Set the extensions we're looking for for conversion
	if options.zipforce:
		CBxMatch='\.[Cc][bB][rRzZ]$'
	else:
		CBxMatch='\.[Cc][bB][rR]$'

	source= os.path.abspath(os.path.expanduser(options.source))
	dest= os.path.abspath(os.path.expanduser(options.dest))

	if source == dest:
		exit("Source = dest {0}".format(source))
		
	#exit() # Safety for testing arg scanner
	# change to dictionary?
	rescount={x:0 for x in ["copy","convert","excluded","failed","skipped"]}
	
	if not os.path.exists(source):
		exit("Error: Source '{0}' does not exist.".format(source))
		
	if os.path.isfile(source):
		# Change around options to handle single file
		options.match=["{0}$".format(re.escape(os.path.basename(source)))]
		#options.match=True
		# options.copy=True # This'll almost always be the required option, make it default?
		source=os.path.dirname(source)
		if options.verbose>1:
			print("** Switching from filemode to dirmode")
			print("** Options:",str(options))
			#print("** Match: {0}".format(match))
	
	if not os.path.isdir(source):
		exit("Error: Source '{0}' is not a file or folder.".format(source))
			
	if options.verbose>1:
		print ("** Process source directory : "+source)
		
	outdir=dest # Default used by FLAT MODE
	
	# All good, already exists		# Check destination is dir (or create)
	# recurse with os.walk()
	failedlist=[]
	
	for root,dirs,files in os.walk(source):
		dirs.sort()
		files.sort()
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
				
			# Continue if excluded by match
			# xor is picky about types so force re.search result into boolean
			if options.match :
				matchflag=False
				for m in options.match:
					if options.ignorecase:
						matcher=re.compile(m, re.I)
					else:
						matcher=m
					if re.search(matcher,infile)!=None:
						matchflag=True
						break
			else:
				matchflag=True

				
			if options.exclude and matchflag:
				for m in options.exclude:
					if options.ignorecase:
						matcher=re.compile(m, re.I)
					else:
						matcher=m
					if re.search(matcher,infile)!=None:
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
			
				
			# Check CBR
			isCBx=re.search(CBxMatch,leaf)
			if not(isCBx or options.copy):
				continue
			
			if not os.path.isdir(outdir):
				if options.whatif:
					print("WHATIF: Create directory {0}".format(outdir))
				else:
					if options.verbose>2:
						print ("**   Creating directory {0}".format(outdir))
					os.makedirs(outdir)

			outfile=os.path.join(outdir,re.sub('\.[Cc][bB][rR]$','.cbz',leaf))
			outfile=outfile.replace(u'\xa0', ' ')
			outfile=outfile.encode('ascii', 'replace').decode('ascii', 'replace')
			
			if os.path.exists(outfile):
				rescount["skipped"] += 1
				if options.verbose>0:
					print("* ResultSkipped: {0}".format(infile))
				continue
			
			if isCBx:
				if options.verbose>2:
					print ("*** CBx extension detected")
				
				if options.whatif:
					print("WHATIF: Convert CBx >cbr2cbz({0},{1})".format(infile,outfile))
				else:
					if options.verbose>0:
						print ("* Converting {0}".format(infile))
					if(cbr2cbz(infile,outfile,verbose=options.verbose,shrink=options.shrink,forceshrink=options.forceshrink,whatif=options.whatif)):
						rescount['convert'] += 1
						if options.verbose>0:
							print("* ResultConvert: {0}".format(infile))
					else:
						rescount['failed'] += 1
						if options.verbose>0:
							print("* ResultFailed: {0}".format(infile))
						failedlist.append(infile)
				continue
			
			# not isCBx so options.copy is set
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
			continue # Next file
							

	# Clean out the temporary folder
	cbr2cbzclean()
	if options.verbose>0:
		print("* Results:",rescount)
		for countkey in rescount.keys():
			print("*  {0}: {1}".format(countkey,rescount[countkey]))
	if options.verbose>1:
		print("** Failed conversions:")
		for failedfile in failedlist:
			print(failedfile)
	
main()
