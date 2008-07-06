#!/usr/bin/python

# debgtd - debian BTS helper tool for users
# Copyright (c) 2008, Jon Dowland <jon@alcopop.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# see "LICENSE" for the full GPL-2.

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
		return (self.user,self.bugs.values())

	def unserialize(self,tuple):
		self.user = tuple[0]
		bugs = tuple[1]
		for bug in bugs:
			self.add_bug(bug)

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
	def __init__(self):

		self.url = 'http://bugs.debian.org/cgi-bin/soap.cgi'
		self.namespace = 'Debbugs/SOAP'

		if os.environ.has_key("http_proxy"):
			my_http_proxy=os.environ["http_proxy"].replace("http://","")
		else:
			my_http_proxy=None

		self.server = SOAPpy.SOAPProxy(self.url, self.namespace,
			http_proxy=my_http_proxy)
		self.needswrite = False

		self.model = None
		self.views = []

	def add_view(self,view):
		if self.model:
			self.model.add_listener(view)
		self.views.append(view)

	def go(self):
		"""and they're off!"""
		if os.environ.has_key("DEBEMAIL"):
			self.set_user(os.environ["DEBEMAIL"])

		for view in self.views:
			# XXX: the view might block, so if we do have more than one,
			# we may only start one at a time.
			view.go()

	def email_to_filename(self):
		"""
			convert the e-mail address used for a model into a
			string suitable for a filename
		"""
		# XXX: can an e-mail address contain characters which
		# are not valid in a filename (e.g. /?)
		if self.model:
			return self.model.user
		return None

	def datafile(self):
		"""calculate the path for the current model's data"""
		if self.model:
			base=os.environ["HOME"] + "/.local/share"
			if "XDG_DATA_HOME" in os.environ:
				base= os.environ["XDG_DATA_HOME"]
			df = base + "/debgtd/" + self.email_to_filename()
			return df 
		return None

	def load_from_file(self):
		fp = open(self.datafile(),"r")
		self.model.unserialize(load(fp))
		fp.close()
		self.needswrite = False

	def save_to_file(self,force=False):
		if not force and self.needswrite:
			# TODO: ensure all the dirs in the path exist
			fp = open(self.datafile(),"w")
			dump(self.model.serialize(),fp)
			fp.close()
			self.needswrite = False

	def import_new_bugs(self):
		"""
			Grab bugs from the BTS that match certain criteria and import
			them into our system.
		"""
		model = self.model
		if not model:
			return
		submitter  = self.server.get_bugs("submitter", model.user)._aslist()
		maintainer = self.server.get_bugs("maint", model.user)._aslist()
		foo = list( set(submitter) | set(maintainer) )
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
	
	def set_user(self, user):
		if self.model and self.model.user == user:
				return
		self.model = Model(user)
		for view in self.views:
			view.clear()
			self.model.add_listener(view)
		if os.path.isfile(self.datafile()):
			self.load_from_file()
