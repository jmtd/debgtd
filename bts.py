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

# the tags we use.
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

		if sleeping not in bug['debgtd']:
			bug['debgtd'].append(sleeping)

		for listener in self.listeners:
			listener.bug_sleeping(bugnum)

	def get_sleeping_bugs(self):
		return [x for x in self.bugs.values() if sleeping in x['debgtd']]
	
	def ignore_bug(self,bugnum):
		bug = self.bugs[bugnum]

		if ignoring not in bug['debgtd']:
			bug['debgtd'].append(ignoring)

		for listener in self.listeners:
			listener.bug_ignored(bugnum)

	def get_ignored_bugs(self):
		return [x for x in self.bugs.values() if ignoring in x['debgtd']]

	def add_listener(self,foo):
		self.listeners.append(foo)

	def add_bug(self,bug):
		self.bugs[bug['id']] = bug
		for listener in self.listeners:
			listener.bug_added(bug)

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
		# remove ones we already know about, if any
		foo = filter(lambda x: x not in self.model.bugs, foo)

		# assume the above executed ok and update our local data
		if 0 < len(foo):
			self.needswrite = True
			self.reload_backend(foo)

	def reload(self):
		model = self.model
		self.reload_backend(usertags[tracking])

	# split off from reload because we'll use it for import too
	# XXX: rename.
	def reload_backend(self, bugs):
		model = self.model
		# fetch the details of all of these bugs
		# christ, someone point me at something which will make the
		# following clear.
		foo = self.server.get_status(bugs)[0]
		if 1 == len(bugs):
			# work around debbts unboxing "feature"
			bug = foo['value']._asdict()
			bug ['debgtd'] = [tracking]
			model.add_bug(bug)
		else:
			for item in foo:
				bug = item['value']._asdict()
				bug['debgtd'] = [tracking]
				model.add_bug(bug)

	# we don't want to track this bug anymore. tag it 'debstd.sleeping'
	def sleep_bug(self,bug):
		self.model.sleep_bug(bug)
		self.needswrite = True

	# we don't want to track this bug anymore, ever. tag it
	def ignore_bug(self,bug):
		self.model.ignore_bug(bug)
		self.needswrite = True
