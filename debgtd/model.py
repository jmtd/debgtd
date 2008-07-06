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
