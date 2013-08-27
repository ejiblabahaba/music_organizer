# -*- coding: utf8 -*-
"""A collection of tools for discovering directory structure, and finding
directories which are in need of repair."""

import bencode
import codecs
import os
import re
import shutil
import tempfile

"""Black magic and shady hacks, do not touch"""
loop = lambda x: range(len(x))
r = r"(.*) \([0-9]{4}\) \[(FLAC|V[0-9]|[0-9]{3}|AAC|WAV|APE|OGG|ABR|WMA|M4A|M4P)\]|Singles"

def writeWrapper(name,data,flag='w'):
	"""Wrapper for writing because I'm tired of juggling fileout flags.

	ARGS:
	name: Name of file in working directory to which data is written.
	data: A list of data to be written.
	flag: Juggled fileout flags. Defaults to 'w'

	RETURNS:
	None.
	"""
	with open(name,flag) as f:
		for x in data:
			x+='\n'
			try:
				f.write(x)
			except UnicodeEncodeError:
				print "The following broke on writing: %s" % x

def _uTorrentMagic():
	"""Open/close utorrent for snapshot read of resume.dat"""
	q = False
	try:
		s = ("C:\\Users\\" + os.getlogin() + 
			"\\AppData\\Roaming\\uTorrent")
		with open(s+'\\resume.dat'): pass
	except IOError:
		raise IOError("Cannot find resume.dat")
	else:
		#is uTorrent on?
		proc_out = Popen('TASKLIST /FI "IMAGENAME eq uTorrent.exe"',
			stdout=PIPE,shell=True).stdout.read()
		if b'uTorrent.exe' in proc_out:
			q = True
			try:
				status = os.system("TASKKILL /IM uTorrent.exe")
			except OSError:
				print "OSError on os.system taskkill of uTorrent..."
			finally:
				if status != 0:
					raise RuntimeError("uTorrent could not be killed.")
	finally:
		f = open(s+'\\resume.dat','rb')
		torrent_data = f.read()
		f.close()
		if q == True:
			status = os.system(s+'\\uTorrent.exe')
			if status != 0:
				raise RuntimeError("uTorrent could not be restarted.")
		return torrent_data

def findPaths(fname=None):
	"""Takes name of torrent resume.dat file, returns all paths. If fname is not
	specified, tries to grab data from utorrent resume.dat file on system using
	os.getlogin(). If resume.dat is not located at the given address, OSError is
	raised. If uTorrent is open, it will be shut down and restarted. 

	ARGS:
	fname - Name or path of input file.

	RETURNS:
	paths: A list of every path found in the file.
	"""
	if fname == None:
		torrent_data = _uTorrentMagic()
	else:
		f = open(fname,'rb')
		torrent_data = f.read()
		f.close()
	data = bencode.bdecode(torrent_data)
	paths = []
	keys = data.keys()
	for i in range(len(keys)):
		try:
			paths.append(data[keys[i]]['path'])
		except TypeError: pass
	paths.sort()
	return paths

def markForbidden(dirs):
	"""Puts an empty file called .STAYOUT in each directory in dirs.

	ARGS:
	dirs - A list of directories with full path names.

	RETURNS:
	None.
	"""
	for path in dirs:
		try:
			with open(path+'\\.STAYOUT','w'): pass
		except:
			head,tail = os.path.split(path)
			try:
				with open(head+'\\.STAYOUT','w'): pass
			except:
				print "%s is broken" % path

def forbid(fname=None):
	"""Clean forbid of all uTorrent dirs. Fname feeds to findPaths."""
	paths = findPaths(fname)
	cwd = os.getcwdu()
	tmpdir = tempfile.mkdtemp()
	os.chdir(tmpdir)
	writeWrapper('torrents.txt',paths)
	with codecs.open('torrents.txt',encoding="UTF-8") as f:
		paths = [line.strip('\r\n') for line in f]
	os.chdir(cwd)
	shutil.rmtree(tmpdir)
	markForbidden(paths)


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
