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

# the usertags we use. these should be changed to something memorable once
# we've settled on a program name, etc.
tracking = "debstd.tracking"
sleeping = "debstd.sleeping"

class Model:
	def __init__(self,user):
		self.user = user
		self.bugs = {}
		self.listeners = []

	def serialize(self):
		return (self.user,self.bugs)

	def unserialize(self,tuple):
		self.user = tuple[0]
		self.bugs = tuple[1]

	def sleep_bug(self,bugnum):
		bug = self.bugs[bugnum]

		if sleeping not in bug['usertags']:
			bug['usertags'].append(sleeping)

		for listener in self.listeners:
			listener.bug_changed(bugnum)

	def get_sleeping_bugs(self):
		return [x for x in self.bugs.values() if sleeping in x['usertags']]

	def add_listener(self,foo):
		self.listeners.append(foo)

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
		self.model.unserialize(load(fp))
		fp.close()
		self.needswrite = False

	def save_to_file(self,file,force=False):
		if not force and self.needswrite:
			fp = open(file,"w")
			dump(self.model.serialize(),fp)
			fp.close()
			self.needswrite = False

	def reload(self):
		model = self.model
		usertags  = self.server.get_usertag(model.user)._asdict()

		# usertag tracking is the master list of bugs we are
		# tracking.
		if not usertags.has_key(tracking):
			sys.stderr.write("error: nothing usertagged needs-attention\n")
			sys.stderr.write("(insert import code here)\n")
			sys.exit(1)

		# fetch the details of all of these bugs
		# christ, someone point me at something which will make the
		# following clear.
		foo = self.server.get_status(usertags[tracking])[0]
		if 1 == len(usertags[tracking]):
			# work around debbts unboxing "feature"
			foo = foo['value']
			model.bugs[foo['id']] = foo._asdict()
		else:
			for item in foo:
				item2 = item['value']
				model.bugs[item2['id']] = item2._asdict()

		# now we need to annotate the bugs with userdata
		sleepingbugs = []
		if usertags.has_key(sleeping):
			sleepingbugs = usertags[sleeping]

		for bug in model.bugs.values():
			bug['usertags'] = [tracking]
			if bug['id'] in sleepingbugs:
				bug['usertags'].append(sleeping)

	# we don't want to track this bug anymore. tag it 'debstd.sleeping'
	# XXX: we may need to shell-escape the model.user string
	def sleep_bug(self,bug):
		os.system("DEBEMAIL=\"%s\" bts usertag %d %s" %
			(self.model.user, bug, sleeping))
		self.model.sleep_bug(bug)
		self.needswrite = True
