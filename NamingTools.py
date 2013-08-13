"""A collection of tools for handling file quality information."""
from mutagen.mp3 import MP3
from mutagen.flac import FLAC

valid_extensions = ('.mp3', '.flac')
u = '$UNKN$'

def getVBRQuality(item):
	"""Takes file and checks VBR quality.

	ARGS:
	item: A path to the file in question.

	RETURNS:
	VBR_quality: An integer in range -1-9, corresponding to VBR quality.
				 -1 represents an unknown value.
	"""
	with open(item, 'rb') as f:
		for i in range(4): #if it isn't in 32MB of data, something's wrong.
			data = f.read(8192)
			index = data.find('LAME3')
			if index != -1:
				quality = ord(data[index - 1])
				VBR_quality = abs((quality + 9) // 10 - 10)
				return VBR_quality
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

def isVBR(item): #dev notes: this should be private in class
	"""Tests whether item is a VBR file, based on mutagen's quality info.
	Occasionally this may be incorrect. There's no way to tell yet.

	ARGS:
	item: A mutagen MP3 object.

	RETURNS:
	A boolean indicating whether item is a VBR file.
	"""
	return ((item.info.bitrate / 1000.) % 8) != 0

def validExtensions(files):
	"""Returns list with only valid extensions.

	ARGS:
	files: A list of strings of file names.

	RETURNS:
	files: A list of strings of file names with valid extensions.
	"""
	rm = [x for x in files if not x.lower().endswith(valid_extensions)]
	for x in range(len(rm)): files.remove(rm[x])
	return files

def addOneToProperty(k,D):
	"""Adds 1 to D[k] if k exists, or sets D[k] to 1. Returns D."""
	if k in D:
		D[k] += 1
	else:
		D[k] = 1
	return D

def getNewFolderName(dr):
	"""Takes a directory, performs mutagen voodoo on each file that has a
	music extension, and returns a suggested folder name.

	ARGS:
	dr: A string with the directory to be renamed.

	RETURNS:
	suggested_name: A string with the suggested rename.
	"""
	files = validExtensions(os.listdir(dr))
	if files == []: return "<no suggestion>"

	albums = {}
	years = {}
	qualities = {}
	rename_props = {'al':albums,'yr':years,'ql':qualities}
	rename_keys = ['al','yr','ql']

	for item in files:
		path = dr + '\\' + item
		if item.lower().endswith('.mp3'): #handles mp3s
			item = MP3(item)
			#album
			album = item.tags.getall('TALB')
			if album != []:
				album = album[0].text[0]
			else:
				album = u
			#year
			year = item.tags.getall('TDRC')
			if year != []:
				year = year[0].text[0]
			else:
				year = u
			#quality
			if isVBR(item):
				VBR_quality = getVBRQuality(item)
				if VBR_quality != -1:	q = 'V' + str(VBR_quality)
				else: q = u
			else:
				q = item.info.bitrate / 1000
		elif item.lower().endswith('.flac'): #handles flacs
			item = FLAC(item)
			q = 'FLAC'
			try:
				year = item['date']
			except KeyError:
				year = u
			try:
				album = item['album']
			except KeyError:
				album = u
		else:
			raise ValueError, "File type not recognized."
		#update dictionaries
		albums = addOneToProperty(album,albums)
		years = addOneToProperty(year,years)
		qualities = addOneToProperty(q,qualities)
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

	suggested_name = '%s (%s) [%s]|%s,%s,%s' % a,b,c,d,e,f
	return suggested_name