# -*- coding: utf8 -*-
"""A collection of tools for handling file quality information."""
from mutagen.mp3 import MP3, HeaderNotFoundError, InvalidMPEGHeader
from mutagen.flac import FLAC, FLACNoHeaderError, FLACVorbisError
from mutagen.m4a import M4A, M4AMetadataError
import os
import re
from FormatTools import writeWrapper as ww

project_dir = os.getcwdu()
valid_extensions = (u'.mp3', u'.flac', u'.m4a', u'.m4p')
u = u'$UNKN$'
r = r"[0-9]{4}"

def getVBRQuality(item):
	"""Takes file and checks VBR quality.

	ARGS:
	item: A path to the file in question.

	RETURNS:
	VBR_quality: An integer in range -1-9, corresponding to VBR quality.
				 -1 represents an unknown value.
	"""
	try:
		with open(item, 'rb') as f:
			for i in range(4): #if it isn't in 32MB of data, something's wrong.
				data = f.read(8192)
				index = data.find('LAME3')
				if index != -1:
					quality = ord(data[index - 1])
					VBR_quality = abs((quality + 9) // 10 - 10)
					return VBR_quality
			return -1
	except IOError:
		print item, "has a fucking weird file name"
		return -1

def consensus(items):
	"""Sorts items by most common value, and returns highest scoring value and
	consensus boolean if all values are the same. In the special case that
	greater than one value is found and this value is not $UNKN$, the next
	most common value is chosen.

	ARGS:
	items: A dict with possible values as keys and quantities as values.

	RETURNS:
	key_val[0][0]: The highest scoring value
	consensus: A boolean indicating whether all values are the same.
	"""
	key_val = [(key, items[key]) for key in items]
	if len(key_val) != 1:
		key_val.sort(key=lambda x: x[1])
		key_val.reverse()
		consensus = False
		#test if $UNKN$ is most popular value
		if key_val[0][0] == u:
			top_score = key_val[1][0]
		else:
			top_score = key_val[0][0]
	else:
		consensus = True
		top_score = key_val[0][0]
	return top_score, consensus

isVBR = lambda item: ((item.info.bitrate / 1000.) % 8) != 0
	"""Tests whether item is a VBR file, returns boolean"""

def validExtensions(files):
	"""Returns list with only valid extensions."""
	rm = [x for x in files if not x.lower().endswith(valid_extensions)]
	for x in range(len(rm)): files.remove(rm[x])
	return files

def addOneToProperty(k,D):
	"""Adds 1 to D[k] if k exists, or sets D[k] to 1. Returns D."""
	try:
		if k in D:
			D[k] += 1
		else:
			D[k] = 1
		return D
	except TypeError, e:
		print "apparently this isn't a dictionary:", D, k
		raise

def getNewFolderName(dr):
	"""Takes a directory, performs mutagen voodoo on each file that has a
	music extension, and returns a suggested folder name.

	ARGS:
	dr: A string with the directory to be renamed.

	RETURNS:
	suggested_name: A string with the suggested rename.
	"""
	os.chdir(dr)
	files = validExtensions(os.listdir(dr))
	if files == []: return "<no suggestion>"

	broken = []
	albums = {}
	years = {}
	qualities = {}
	rename_props = {'al':albums,'yr':years,'ql':qualities}
	rename_keys = ['al','yr','ql']

	for item in files:
		try:
			name_copy = str(item)
		except UnicodeEncodeError, e:
			print "broke on item ", item
			print "Attempting unicode magic"
			name_copy = str(item.encode('utf8','replace'))
		path = dr + '\\' + item
		if item.lower().endswith('.mp3'): #handles mp3s
			try:
				item = MP3(item)
				#album
				try:
					album = item.tags.getall('TALB')
				except AttributeError:
					print name_copy," has weird fuckin album tags"
					album = []
					broken.append(os.path.join(dr,name_copy))
				if album != []:
					album = str(album[0].text[0])
				else:
					album = u
				#year
				try:
					year = item.tags.getall('TDRC')
				except AttributeError:
					print name_copy," has weird fuckin date tags"
					year = []
					broken.append(os.path.join(dr,name_copy))
				if year != []:
					year = str(year[0].text[0])
					if len(year) != 4:
						yl = re.findall(r,year)
						if yl != []: year = yl[0]
						else: year = u
				else:
					year = u
				#quality
				if isVBR(item):
					VBR_quality = getVBRQuality(name_copy)
					if VBR_quality != -1: q = 'V' + str(VBR_quality)
					else: q = u
				else:
					q = item.info.bitrate / 1000
			except HeaderNotFoundError:
				print "No header found on ", item, ", skipping..."
				broken.append(os.path.join(dr,item))
		elif item.lower().endswith('.flac'): #handles flacs
			try:
				item = FLAC(item)
				q = 'FLAC'
				try:
					year = item['date'][0]
					if len(year) != 4:
						yl = re.findall(r,year)
						if yl != []: year = yl[0]
						else: year = u
				except KeyError:
					year = u
				try:
					album = item['album'][0]
				except KeyError:
					album = u
			except FLACNoHeaderError:
				print "No header found on ", item, ", skipping..."
				broken.append(os.path.join(dr,item))
		elif item.lower().endswith('.m4a') or item.lower().endswith('m4p'):
			try:
				if item.lower().endswith('.m4a'): q = 'M4A'
				else: q = 'M4P'
				item = M4A(item)
				try:
					year = item.tags['\xa9day']
					if len(year) != 4:
						yl = re.findall(r,year)
						if yl != []: year = yl[0]
						else: year = u
				except KeyError:
					year = u
				try:
					album = item.tags['\xa9alb']
				except KeyError:
					album = u
			except:
				print "A dumb thing happened on", item, ", whatever"
				broken.append(os.path.join(dr,item))
		else:
			raise ValueError, "File type not recognized."
		#update dictionaries
		try:
			albums = addOneToProperty(album,albums)
			years = addOneToProperty(year,years)
			qualities = addOneToProperty(q,qualities)
		except TypeError, e:
			print "broke on file ", name_copy
			raise
	report = {}
	for key in rename_keys:
		if rename_props[key] != {}:
			report[key], report[key + '_report'] = consensus(rename_props[key])
		else:
			name_vals[key] = u
			report[key + '_report'] = 'Error'

	a = report['al']
	b = report['yr']
	c = report['ql']
	d = report['al_report']
	e = report['yr_report']
	f = report['ql_report']

	seen = set()
	seen_add = seen.add
	unique_broken = [x for x in broken if x not in seen and not seen_add(x)]
	ww(project_dir + '\\broken.txt',unique_broken)

	suggested_name = '%s (%s) [%s]|%s,%s,%s' % (a,b,c,d,e,f)
	return suggested_name

def createSuggestions(dirs):
	"""Creates suggestions for every dir in dirs.

	ARGS:
	dirs: A list of dirs in need of fixing.

	YIELDS:
	suggestion: a string containing the original directory and a suggestion for
		a rename. An example is below:

		oldpath$album (year) [codec]|album,year,quality reports
	"""
	for i in range(len(dirs)):
		try:
			output = str(dirs[i])+u'?'+getNewFolderName(dirs[i])
		except UnicodeEncodeError:
			print "this fucker keeps breaking everything"
			print dirs[i]
		yield output

def rename(proposed):
	"""Takes proposals and renames them.

	ARGS:
	propsed - a list of proposals, formatted such:
		<old full path>$$$<new dir stub>

	RETURNS:
	None.
	"""
	try:
		for line in proposed:
			sep = line.find(u"?")
			old = line[:sep]
			dst = line[sep+1:].strip("\n")
			l = old.split("\\")
			src = l.pop()
			path = ""
			for item in l:
				path += item + "\\"
			os.chdir(path)
			os.rename(src,dst)
	except:
		print "%s fucked up" % line
	finally:
		print "Job's done."

makeClean = lambda proposed: [item for item in proposed if u not in item]
"""Scrubs proposed dirs for unknown string, and removes them."""
makeUnclean = lambda proposed: [item for item in proposed if u in item]
"""Scrubs proposed dirs if unknown string is not present."""