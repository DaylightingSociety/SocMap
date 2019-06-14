#!/usr/bin/env python3

import queue, sys, datetime

err = 0
ERR = 0
ERROR = 0
warn = 1
WARN = 1
WARNING = 1
info = 2
INFO = 2
INFORMATION = 2
debug = 3
DEBUG = 3

logbuffer = queue.Queue()

def logHandler(workdir, filename, debug):
	if( filename == None ):
		logfile = sys.stdout
	# Check for absolute path (logfile starts with '/')
	elif( len(filename) > 0 and filename[0] == "/" ):
		logfile = open(filename, "w")
	else:
		logfile = open(workdir + "/" + filename, "w")
	while(True):
		(level, msg) = logbuffer.get()
		time = datetime.datetime.now().strftime("%D %H:%M:%S")
		if( level == ERR ):
			logfile.write(time + " ERROR: " + msg + "\n")
		elif( level == WARN ):
			logfile.write(time + " WARNING: " + msg + "\n")
		elif( level == INFO ):
			logfile.write(time + " Info: " + msg + "\n")
		elif( level == DEBUG and debug ):
			logfile.write(time + " Debug: " + msg + "\n")
		logfile.flush()

def log(level, msg):
	logbuffer.put((level, msg))
