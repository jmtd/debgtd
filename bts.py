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
tracking = "debgtd.tracking"
sleeping = "debgtd.sleeping"
ignoring = "debgtd.ignoring"

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
	
	def ignore_bug(self,bugnum):
		bug = self.bugs[bugnum]

		if ignoring not in bug['usertags']:
			bug['usertags'].append(ignoring)

		for listener in self.listeners:
			listener.bug_changed(bugnum)

	def get_ignored_bugs(self):
		return [x for x in self.bugs.values() if ignoring in x['usertags']]

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

	def import_new_bugs(self):
		"""
			Grab bugs from the BTS that match certain criteria and import
			them into our system.
		"""
		model = self.model
		foo = self.server.get_bugs("submitter", model.user)
		usertags = self.server.get_usertag(model.user)._asdict()
		# remove ones we already know about
		foo = filter(lambda x: x not in self.model.bugs, foo)

		# nothing to do?
		if 0 == len(foo):
			return

		# any bugs not already usertagged should be marked tracking
		# for now, don't actually execute this
		foo2 = filter(lambda x: x not in usertags[tracking], foo)
		if 0 < len(foo2):
			execme = "bts " + \
				" , ".join(map(lambda b: "usertag %d + %s"%(b,tracking), foo2))
			print execme

		# assume the above executed ok and update our local data
		self.reload_backend(foo)

	def reload(self):
		model = self.model
		usertags = self.server.get_usertag(model.user)._asdict()

		# usertag tracking is the master list of bugs we are
		# tracking.
		if not usertags.has_key(tracking):
			sys.stderr.write("error: nothing usertagged %s\n"% tracking)
			sys.stderr.write("(insert import code here)\n")
			sys.exit(1)

		self.reload_backend(usertags[tracking])

	# split off from reload because we'll use it for import too
	# XXX: rename.
	def reload_backend(self, bugs):
		model = self.model
		usertags = self.server.get_usertag(model.user)._asdict()
		# fetch the details of all of these bugs
		# christ, someone point me at something which will make the
		# following clear.
		foo = self.server.get_status(bugs)[0]
		if 1 == len(bugs):
			# work around debbts unboxing "feature"
			foo = foo['value']
			model.bugs[foo['id']] = foo._asdict()
		else:
			for item in foo:
				item2 = item['value']
				model.bugs[item2['id']] = item2._asdict()

		# now we need to annotate the bugs with userdata
		# (the BTS doesn't include it in the bugs y'see)
		sleepingbugs = []
		if usertags.has_key(sleeping):
			sleepingbugs = usertags[sleeping]

		ignoredbugs = []
		if usertags.has_key(ignoring):
			ignoredbugs = usertags[ignoring]

		for bug in model.bugs.values():
			bug['usertags'] = [tracking]
			if bug['id'] in sleepingbugs:
				bug['usertags'].append(sleeping)
			if bug['id'] in ignoredbugs:
				bug['usertags'].append(ignoring)

	# we don't want to track this bug anymore. tag it 'debstd.sleeping'
	# XXX: we may need to shell-escape the model.user string
	def sleep_bug(self,bug):
		os.system("DEBEMAIL=\"%s\" bts usertag %d %s" %
			(self.model.user, bug, sleeping))
		self.model.sleep_bug(bug)
		self.needswrite = True

	# we don't want to track this bug anymore, ever. tag it
	# XXX: we may need to shell-escape the model.user string
	def ignore_bug(self,bug):
		os.system("DEBEMAIL=\"%s\" bts usertag %d %s" %
			(self.model.user, bug, ignoring))
		self.model.ignore_bug(bug)
		self.needswrite = True
