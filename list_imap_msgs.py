#!/usr/bin/python
# -*- coding: utf-8 -*-
import os,sys,getpass,time
import imaplib
import email.header
IMAPSERVER=""
IMAPPORT="993"
IMAPUSER=""
IMAPPASSWORD=""
IMAPMAILBOX=""
SSL=False
DEBUG=0
FIELDS=list()
def Message(text):
	global DEBUG
	date=time.time()
	message="%s %s" % (date,text)
	if DEBUG > 0:
		print message
def FieldToShow(FIELD):
	global FIELDS
	for SFIELD in FIELDS:
		if FIELD == SFIELD:
			return True
	return False
def ProcessArguments():
	global DEBUG,IMAPSERVER,IMAPPORT,IMAPUSER,IMAPPASSWORD,IMAPMAILBOX,SSL,FIELDS
	for arg in sys.argv:
		if arg=="-h" or arg=="--help" or arg=="-?" or arg=="/?" or arg=="/h" or arg=="/help":
			Usage()
			sys.exit(0)
		if arg=="-d":
			DEBUG=DEBUG+1
			Message("Debug level incressed")
		if arg.lower()=="--ssl":
			Message("Will use SSL")
			SSL=True
		if arg.lower()=="-s":
			Message("Will use SSL")
			SSL=True
		larg=arg.split("=",1)
		if len(larg)==2:
			if larg[0].lower()=="--field":
				FIELDS.append(larg[1])
			if larg[0].lower()=="--imap-server":
				Message("Server will be '%s'" % larg[1])
				IMAPSERVER=larg[1]
			if larg[0].lower()=="--imap-port":
				Message("Port will be '%s'" % larg[1])
				IMAPPORT=larg[1]
			if larg[0].lower()=="--imap-user":
				Message("User will be '%s'" % larg[1])
				IMAPUSER=larg[1]
			if larg[0].lower()=="--imap-password":
				if larg[1] != "":
					Message("Password is set")
				IMAPPASSWORD=larg[1]
			if larg[0].lower()=="--imap-mailbox":
				Message("Mailbox will be '%s'" % larg[1])
				IMAPMAILBOX=larg[1]
			if larg[0].lower()=="--imap-password-file":
				Message("Reading password from file '%s'" % larg[1])
				if os.path.exists(larg[1]):
					FILE=open(larg[1],"r")
					IMAPPASSWORD=FILE.readline().replace("\n","").replace("\r","")
					FILE.close()
				else:
					print "The password file '%s' doesn't exists" % larg[1]
					sys.exit(65)
	if IMAPPASSWORD == "":
		IMAPPASSWORD=getpass.getpass("Password for '%s@%s:%s': " % (IMAPUSER,IMAPSERVER,IMAPPORT))
	#Message("Password will be '%s'" % IMAPPASSWORD)
	if IMAPSERVER == "":
		print "You must indicate a server to connecto to"
		Usage()
		sys.exit(65)
	if IMAPUSER == "":
		print "You must indicate a username"
		Usage()
		sys.exit(65)
	if IMAPMAILBOX == "":
		print "You must indicate a mailbox in the server"
		Usage()
		sys.exit(65)
def Usage():
	print "%s [-h] [-d] [--field=FieldName1] [--field=FieldName2] [--field=FieldName3] [--field=FieldNameN] [--imap-server=IMAPSERVER --imap-port=IMAPPORT --imap-user=IMAPUSER --imap-password=IMAPPASSWORD --imap-password-file=IMAPPASSWORDFILE --imap-mailbox=IMAPMAILBOX] [--ssl|-s]" % sys.argv[0]
ProcessArguments()
if len(FIELDS)==0:
	FIELDS.append("Subject")
if SSL:
	PROTO="imaps"
else:
	PROTO="imap"
Message("Connecting to %s://%s:%s/ ..." % (PROTO,IMAPSERVER,IMAPPORT))
if SSL:
	try:
		IMAP=imaplib.IMAP4_SSL(IMAPSERVER, IMAPPORT)
	except:
		print "Error connecting to '%s:%s'." % (IMAPSERVER,IMAPPORT)
		sys.exit(1)
else:
	try:
		IMAP=imaplib.IMAP4(IMAPSERVER, IMAPPORT)
	except:
		print "Error connecting to '%s:%s'." % (IMAPSERVER,IMAPPORT)
		sys.exit(1)
Message("Identifying...")
try:
	IMAP.login(IMAPUSER,IMAPPASSWORD)
except imaplib.IMAP4.error, e:
	print "Error login as '%s@%s:%s'. %s" % (IMAPUSER,IMAPSERVER,IMAPPORT,e)
	#IMAP.close()
	IMAP.logout()
	sys.exit(1)
Message("Selecting mailbox %s..." % IMAPMAILBOX)
try:
	STATUS,DATA=IMAP.select(IMAPMAILBOX,True)
except imaplib.IMAP4.error, e:
	print "Error selecting mailbox '%s@%s:%s/%s'. Server message: %s"  % (IMAPUSER,IMAPSERVER,IMAPPORT,IMAPMAILBOX,e)
	IMAP.close()
	IMAP.logout()
	sys.exit(1)
if STATUS == "NO":
	DEBUG=DEBUG + 1
	Message("Server report an error selecting mailbox. Server response: %s" % DATA[0])
else:
	Message("Looking for messages...")
	try:
		TYPE, DATA=IMAP.search(None,"ALL")
	except imaplib.IMAP4.error, e:
		print "Error looking for messages in mailbox '%s://%s@%s:%s/%s'. Server message: %s"  % (PROTO,IMAPUSER,IMAPSERVER,IMAPPORT,IMAPMAILBOX,e)
		IMAP.logout()
		sys.exit(1)
	Message("Data received: %s" % DATA)
	for ID in DATA[0].split():
		try:
			TYPE,DATA = IMAP.fetch(ID, '(BODY[HEADER])')
		except:
			print "Error fetching messages headers"
			IMAP.close()
			IMAP.logout()
			sys.exit(1)
		NEWDATA=DATA[0][1].replace("\r","").replace("\n "," ").replace("\n\t"," ")
		HEADERS=NEWDATA.splitlines()
		for HEADER in HEADERS:
			LHEADER=HEADER.split(": ",1)
			if FieldToShow(LHEADER[0]):
				DECSUBJECTS=email.header.decode_header(LHEADER[1])
				SUBJECT=""
				for DECSUBJECT in DECSUBJECTS:
					PARTIALSUBJECT,ENCODING=DECSUBJECT
					if ENCODING == None:
						SUBJECT="%s %s" % (SUBJECT,PARTIALSUBJECT)
					else:
						SUBJECT='%s %s' % (SUBJECT, PARTIALSUBJECT.decode(ENCODING,"replace"))
				try:
					print 'Message %s:%s' % (ID, SUBJECT.encode("utf8","replace"))
				except UnicodeDecodeError:
					print 'Message %s:%s' % (ID, SUBJECT.decode('iso-8859-1').encode('utf8','replace'))
	IMAP.close()
IMAP.logout()
