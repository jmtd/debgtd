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
import debgtd
from pickle import load, dump
from debgtd.model import Model

class Controller:
	def __init__(self):

		self.url = 'http://bugs.debian.org/cgi-bin/soap.cgi'
		self.namespace = 'Debbugs/SOAP'

		if os.environ.has_key("http_proxy"):
			my_http_proxy=os.environ["http_proxy"].replace("http://","")
			if my_http_proxy[-1] == '/':
				my_http_proxy = my_http_proxy[:-1]
		else:
			my_http_proxy=None

		self.server = SOAPpy.SOAPProxy(self.url, self.namespace,
			http_proxy=my_http_proxy)
		self.needswrite = False

		self.model = None
		self.views = []

		# read in configuration data
		self.confdata_format = 1

		base=os.environ["HOME"] + "/.config"
		if "XDG_CONFIG_HOME" in os.environ:
			base= os.environ["XDG_CONFIG_HOME"]
		self.conffile = base + "/debgtd/" + "config"
		self.confdata = {}
		if os.path.isfile(self.conffile):
			fp = open(self.conffile)
			data = load(fp)
			fp.close()
			self.confdata = data[1]

	def add_view(self,view):
		if self.model:
			self.model.add_listener(view)
		self.views.append(view)

	def go(self):
		"""and they're off!"""
		if os.environ.has_key("DEBEMAIL") and '' != os.environ['DEBEMAIL']:
			self.set_user(os.environ["DEBEMAIL"])
		else:
			if "user" in self.confdata:
				print "using saved config info"
				self.set_user(self.confdata['user'])

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
			df = self.datafile()

			# TODO: it would be nicer to use pure python here
			dirname = os.path.dirname(df)
			if not os.path.isdir(dirname):
				os.system("mkdir -p %s" % dirname)

			fp = open(df,"w")
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
			bug ['debgtd'] = [debgtd.tracking] # TODO: remove
			model.add_bug(bug)
		else:
			for item in foo:
				bug = item['value']._asdict()
				bug['debgtd'] = [debgtd.tracking] # TODO: remove
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
			view.user_changed(user)
			self.model.add_listener(view)
		if os.path.isfile(self.datafile()):
			self.load_from_file()

		# write out configuration data if necessary
		if not ("user" in self.confdata and user == self.confdata['user']):
			self.confdata['user'] = user

			# TODO: would be nice to have pure python here
			dirname = os.path.dirname(self.conffile)
			if not os.path.isdir(dirname):
				os.system("mkdir -p %s" % dirname)

			fp = open(self.conffile, "w")
			data = dump((self.confdata_format, self.confdata), fp)
			fp.close()

