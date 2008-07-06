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
import debgtd
from pickle import load, dump

# serialize_format will be used to be backwards-compatible
# whenever we change the serialize or unserialize methods
serialize_format = 1

class Model:
	def __init__(self,user):
		self.user = user
		self.bugs = {}
		self.listeners = []

	def serialize(self):
		return (serialize_format, self.user, self.bugs.values())

	# TODO: should consider handling serialize_format
	def unserialize(self,tuple):
		self.user = tuple[1]
		bugs = tuple[2]
		for bug in bugs:
			self.add_bug(bug)

	def sleep_bug(self,bugnum):
		bug = self.bugs[bugnum]

		if debgtd.sleeping not in bug['debgtd']:
			bug['debgtd'].append(debgtd.sleeping)

		for listener in self.listeners:
			listener.bug_sleeping(bugnum)

	def get_sleeping_bugs(self):
		return [x for x in self.bugs.values() if debgtd.sleeping in x['debgtd']]
	
	def ignore_bug(self,bugnum):
		bug = self.bugs[bugnum]

		if debgtd.ignoring not in bug['debgtd']:
			bug['debgtd'].append(debgtd.ignoring)

		for listener in self.listeners:
			listener.bug_ignored(bugnum)

	def get_ignored_bugs(self):
		return [x for x in self.bugs.values() if debgtd.ignoring in x['debgtd']]

	def add_listener(self,foo):
		self.listeners.append(foo)

	def add_bug(self,bug):
		self.bugs[bug['id']] = bug
		for listener in self.listeners:
			listener.bug_added(bug)
