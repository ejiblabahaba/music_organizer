# -*- coding: utf8 -*-
"""A collection of tools for discovering directory structure, and finding
directories which are in need of repair."""

import os
import re

"""Black magic and shady hacks, do not touch"""
loop = lambda x: range(len(x))
r = r"(.*) \([0-9]{4}\) \[(FLAC|V[0-9]|[0-9]{3}|AAC|WAV|APE|OGG|ABR|WMA)\]|Singles"

def writeWrapper(name,data):
	"""Wrapper for writing because I'm tired of juggling fileout flags.

	ARGS:
	name: Name of file in working directory to which data is written.
	data: A list of data to be written.

	RETURNS:
	None.
	"""
	with open(name,'a') as f:
		for x in data:
			try:
				f.write(x + '\n')
			except UnicodeEncodeError:
				try:
					f.write(x.encode('utf8','replace') + '\n')
				except UnicodeEncodeError:
					print "The following broke on writing: %s" % x

def getIgnores(ignore_str, path="Z:\\", dirs=None, specials=None):
	"""Returns directories that are ignored, based on starting character.
	By default, automatically ignores directories beginning with '$', and the
	System Volume Information. If fileout is set, writes list to a file.

	ARGS:
	ignore_str: A string used at the start of folders to be ignored.
	path: Top level directory to search. Defaults to Z:\\.
	dirs: If provided, dirs allows getIgnores() to skip an extra os.walk()
	cycle, which is faster. Defaults to None. 
	specials: A list with any special items to ignore. Defaults to None.

	RETURNS:
	ignore: list of directories to ignore at the top level.
	"""
	if dirs == None:
		path, dirs, files = next(os.walk(path))
		del(files)
	ignore= [x for x in dirs if x.startswith(ignore_str) or x.startswith('$')]
	ignore.append('System Volume Information')
	if specials != None:
		ignore += [n for n in specials]
	return ignore

def walkToDepth(depth=1,path=u'Z:\\'):
	"""Gets complete directory structure at the specified level. Useful when
	pure os.walk() would delve too deep.

	ARGS:
	depth: Recursive depth to pursue. Defaults to 1.
	path: Root directory. Defaults to Z:\\.

	RETURNS:
	all_paths: A list of all paths to the specified depth.
	"""
	all_paths = []
	path, dirs, files = next(os.walk(path))
	del(files)
	
	ignore = getIgnores('-',path=path,dirs=dirs,
		specials=['Singles','Kyle Landry','Seraphim','Various Artists'])
	for x in loop(ignore):
		try:
			dirs.remove(ignore[x])
		except ValueError:
			pass

	if depth == 1:
		return dirs
	else:
		for x in loop(dirs):
			all_paths += [os.path.join(path,dirs[x],y) for y in walkToDepth(
				depth=depth-1, path=os.path.join(path,dirs[x]))]
		return all_paths

def getUnformattedFolders(path=u'Z:\\',dirs=None):
	"""Gets folders which need to be fixed.

	ARGS:
	path: Top level directory containing artists. Defaults to Z:\\.
	dirs: If specified, searches directories in dirs. In implementation, the
		function builds its dirs list using the getDirStruct() function. If
		that function has already been performed, use its return for speedup.
		Defaults to None.

	RETURNS:
	fixlist: A list of directories which require correction.
	"""
	fixlist = []
	if dirs == None:
		dirs = walkToDepth(depth=2,path=path)
	match = [re.search(r, dirs[x]) for x in loop(dirs)]
	fixlist += [dirs[x] for x in loop(dirs) if not match[x]]
	return fixlist

def _extLoop(files, path, items):
	"""Extension loop subroutine."""
	if files != []:
			for i in loop(files):
				root, ext = os.path.splitext(os.path.join(path,files[i]))
				ext = ext.lower()
				if ext not in items and len(ext) < 6: items.append(ext)
	return items

def _fileLoop(files, path, items):
	"""File loop subroutine."""
	items += [os.path.join(path,f) for f in files]
	return items

def getFileInfo(path=u"Z:\\",dirs=None, fx=_extLoop):
	"""Gets all files or extensions in a given directory, dependent on the
	function applied.

	ARGS:
	path: Top level path for os.walk(). Defaults to Z:\\.
	dirs: If specified, gets all items in only the directories in dirs.
	fx: Pointer to function to be applied.

	RETURNS:
	items: A list of all items found.
	"""

	items = []
	if dirs == None:
		w = os.walk(path)
		while True:
			try:
				top, sub, files = next(w)
			except StopIteration:
				break
			items = fx(files,top,items)
	else:
		for item in dirs:
			items = fx(os.listdir(item),item,items)

	if '' in items: items.remove('')
	return items
