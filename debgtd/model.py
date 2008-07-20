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

import os
import sys
import datetime
import debgtd
from pickle import load, dump

# serialize_format will be used to be backwards-compatible
# whenever we change the serialize or unserialize methods
serialize_format = 3

class Bug(dict):
	def __init__(self, hash={}):
		dict.__init__(self)

		self._ignoring = False
		self._sleeping = False
		self._nextaction = None

		hash and self.update_hash(hash)

	def update_hash(self,hash):
		for key in hash:
			self[key] = hash[key]

	def sleep(self,slept_at=datetime.datetime.now()):
		self._sleeping = True
		self.slept_at = slept_at

	def sleeping(self):
		return self._sleeping

	def wake(self):
		self._sleeping = False

	def ignore(self):
		self._ignoring = True

	def ignoring(self):
		return self._ignoring

	def unignore(self):
		self.ignoring = False

	def has_nextaction(self):
		return self._nextaction != None
	
	def set_nextaction(self, na):
		self._nextaction = na

	def get_nextaction(self):
		return self._nextaction

	def is_done(self):
		return self['done'] != ''

class Model:
	def __init__(self,user):
		self.user = user
		self.bugs = {}
		self.listeners = []

	def serialize(self):
		return (serialize_format, self.user, self.bugs.values())

	# TODO: should consider handling serialize_format
	def unserialize(self,tuple):
		fmt = tuple[0]
		self.user = tuple[1]

		# convert pure-hash format to class-and-hash
		if fmt == 1:
			for hash in tuple[2]:
				bug = Bug(hash)
				if 'debgtd.sleeping' in bug['debgtd']:
					if 'debgtd.slept_at' in bug['debgtd']:
						index = bug['debgtd'].index('debgtd.slept_at')
						date = bug['debgtd'][index]
						del bug['debgtd'][index]
						bug.sleep(date)
					else:
						bug.sleep()
					index = bug['debgtd'].index('debgtd.sleeping')
					del bug['debgtd'][index]
				if 'debgtd.ignoring' in bug['debgtd']:
					bug.ignore()
					index = bug['debgtd'].index('debgtd.ignoring')
					del bug['debgtd'][index]
				if 'debgtd.tracking' in bug['debgtd']:
					index = bug['debgtd'].index('debgtd.tracking')
					del bug['debgtd'][index]
				if [] != bug['debgtd']:
					print "weird, found the following:"
					print bug['debgtd']
				else:
					del bug['debgtd']
				self.add_bug(bug)

		elif fmt >= 2:
			bugs = tuple[2]
			for bug in bugs:
				self.add_bug(bug)
		else:
			sys.stderr.write("unsupported format %d\n" % fmt)
			sys.exit(1)

		if fmt < 3:
			for bug in bugs:
				if not hasattr(bug, '_nextaction'):
					bug.set_nextaction(None)

	def sleep_bug(self,bugnum):
		bug = self.bugs[bugnum]
		bug.sleep()

		for listener in self.listeners:
			listener.bug_sleeping(bug)

	def get_sleeping_bugs(self):
		return [x for x in self.bugs.values() if x.sleeping()]
	
	def ignore_bug(self,bugnum):
		bug = self.bugs[bugnum]
		bug.ignore()

		for listener in self.listeners:
			listener.bug_ignored(bug)

	def get_ignored_bugs(self):
		return [x for x in self.bugs.values() if x.ignoring()]

	def add_listener(self,foo):
		self.listeners.append(foo)

	def add_bug(self,bug):
		self.bugs[bug['id']] = bug
		for listener in self.listeners:
			listener.bug_added(bug)

	def update_bug(self, hash):
		bug = self.bugs[hash['id']]
		# this relies on the Bug class still comparing like dicts
		if bug != hash: 
			bug.update_hash(hash)
			for listener in self.listeners:
				listener.bug_changed(bug)
