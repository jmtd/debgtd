#!/usr/bin/python
# see http://wiki.debian.org/DebbugsSoapInterface

import SOAPpy
import os
import sys
from pickle import load, dump

severities = {
	"wishlist" : 0,
	"minor"    : 1,
	"normal"   : 2,
	"important": 3,
	"serious"  : 4,
	"grave"    : 5,
	"critical" : 6,
}

class Model:
	def __init__(self):
		self.user = "jon+bts@alcopop.org"
		self.usertags = {}    # an internal, semi-private structure
		self.bugs = {}        # public hash of all known bugs
		self.tracking = set() # bugs we are tracking (all of 'em)
		self.interested = set() # bugs we wish to display
		self.sleeping = set() # bugs that are being slept

class Controller:
	def __init__(self,model):

		self.url = 'http://bugs.debian.org/cgi-bin/soap.cgi'
		self.namespace = 'Debbugs/SOAP'

		self.model = model

		if os.environ.has_key("http_proxy"):
			my_http_proxy=os.environ["http_proxy"].replace("http://","")
		else:
			my_http_proxy=None

		self.server = SOAPpy.SOAPProxy(self.url, self.namespace,
			http_proxy=my_http_proxy)
		self.needswrite = False

	def load_from_file(self,file):
		fp = open(file,"r")
		self.model = load(fp)
		fp.close()
		self.needswrite = False

	def save_to_file(self,file,force=False):
		if not force and self.needswrite:
			fp = open(file,"w")
			dump(self.model,fp)
			fp.close()
			self.needswrite = False

	def reload(self):
		model = self.model
		model.usertags  = self.server.get_usertag(model.user)._asdict()

		# usertag "needs-attention" is the master list of bugs we are
		# tracking.
		if not model.usertags.has_key("needs-attention"):
			sys.stderr.write("error: nothing usertagged needs-attention\n")
			sys.exit(1)
		model.tracking = set(model.usertags['needs-attention'])

		# there is a separate list of bugs we are interested in, at this
		# point in time, because we may be ignoring some.
		model.interested = model.tracking.copy()

		# are we ignoring any sleeping bugs?
		if model.usertags.has_key("debstd.sleeping"):
			foo = set(model.usertags['debstd.sleeping'])
			model.interested -= foo
			model.sleeping = foo
		else:
			print "debug: no sleeping bugs"

		# fetch the status of all bugs we are dealing with.
		foo = self.server.get_status([x for x in model.tracking])
		for item in foo[0]:
			model.bugs[item[1]['id']] = item[1]._asdict()

	# we don't want to track this bug anymore. tag it 'debstd.sleeping'
	# XXX: we may need to shell-escape the model.user string
	def sleep_bug(self,bug):
		os.system("DEBEMAIL=\"%s\" bts usertag %d debstd.sleeping" %
			(self.model.user, bug))
		del self.model.bugs[bug]
		self.needswrite = True
