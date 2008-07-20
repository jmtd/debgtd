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

import sys
import gtk
import gtk.glade
import os

import debgtd
from debgtd.controller import Controller

class TriageWindow:
	def __init__(self,controller,gladefile):
		self.controller = controller
		self.wTree = gtk.glade.XML(gladefile,"triage_window")
		window = self.wTree.get_widget("triage_window")
		window.resize(640,400)

		# signals
		window.connect("destroy", lambda x: self.close)
		self.wTree.get_widget("closebutton").connect("clicked",
			lambda x: self.close)
		self.wTree.get_widget("applybutton").connect("clicked",
			self.apply_button)
		self.wTree.get_widget("sleepbutton").connect("clicked",
			self.sleep_button)
		self.wTree.get_widget("ignorebutton").connect("clicked",
			self.ignore_button)

		# initialisation
		self.processed = 0
		self.target = 0

		self.get_next_bug()
		window.show()

	def close(self):
		self.processed = 0
		self.target    = 0
		self.wTree.get_widget("triage_window").hide()

	def get_next_bug(self):
		bugs_todo = filter(lambda b: \
		not b.has_nextaction() and not b.ignoring() and not b.sleeping() and
		not b.is_done(),
			self.controller.model.bugs.values())
		self.current_bug = bugs_todo[0]
		buf = self.wTree.get_widget("nextaction").get_buffer()
		buf.delete(buf.get_start_iter(), buf.get_end_iter())
		if not self.target:
			self.target = len(bugs_todo)
		self.update_currentbug()
		self.update_progress()

	def apply_button(self,button):
		buf = self.wTree.get_widget("nextaction").get_buffer()
		text = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
		self.controller.set_nextaction(self.current_bug, text)
		self.processed += 1
		self.get_next_bug()

	def sleep_button(self,button):
		self.controller.sleep_bug(self.current_bug['id'])
		self.processed += 1
		self.get_next_bug()

	def ignore_button(self,button):
		self.controller.ignore_bug(self.current_bug['id'])
		self.processed += 1
		self.get_next_bug()

	def update_currentbug(self):
		buginfo = self.wTree.get_widget("summarybutton")
		buginfo.set_label(self.current_bug['subject'])
		buginfo.connect("clicked", lambda x: \
			os.system("sensible-browser http://bugs.debian.org/%s &" \
			% self.current_bug['id']))

	def update_progress(self):
		progressbar = self.wTree.get_widget("progressbar")
		progresslabel = self.wTree.get_widget("progresslabel")
		progresslabel.set_text("%d / %d" % (self.processed, self.target))
		progressbar.set_fraction( float(self.processed) / float(self.target) )

class Gui:
	def __init__(self,controller):
		self.controller = controller

		if os.path.isfile("debgtd.glade"):
			self.gladefile = "debgtd.glade"
		elif os.path.isfile("/usr/local/share/debgtd/debgtd.glade"):
			self.gladefile = "/usr/local/share/debgtd/debgtd.glade"
		else:
			self.gladefile = "/usr/share/debgtd/debgtd.glade"

		self.wTree = gtk.glade.XML(self.gladefile,"window1")

		window = self.wTree.get_widget("window1")
		window.resize(800,600)
		window.show()
		self.wTree.get_widget("quit_menu_item").connect("activate", gtk.main_quit)
		self.wTree.get_widget("window1").connect("destroy", gtk.main_quit)

		self.tree = self.wTree.get_widget("treeview1")
		self.tree.connect("row-activated", self.row_selected_cb)
		self.populate_treeview()

		button = self.wTree.get_widget("sleep_bug_button")
		button.connect("clicked", self.sleep_cb)
		self.wTree.get_widget("sleep_menu_item").connect("activate",
			self.sleep_cb)
		button = self.wTree.get_widget("refresh_data_button")
		button.connect("clicked", self.refresh_data_cb)

		button = self.wTree.get_widget("ignore_bug_button")
		button.connect("clicked", self.ignore_cb)
		self.wTree.get_widget("ignore_menu_item").connect("activate",
			self.ignore_cb)

		button = self.wTree.get_widget("triage_button")
		button.connect("clicked", self.open_triage_window)

	def open_triage_window(self,button):
		tw = TriageWindow(self.controller,self.gladefile)

	def update_summary_label(self):
		model = self.controller.model
		label = self.wTree.get_widget("num_bugs_label")

		total = len(filter(lambda bug: not bug.is_done(), model.bugs.values()))
		# XXX BUG there might be an intersection between these
		# should use real set logic instead of arithmetic
		sleeping = len(model.get_sleeping_bugs())
		ignored = len(model.get_ignored_bugs())
		interested = total - sleeping - ignored

		label.set_text("%d bugs (%d sleeping; %d ignored)" % \
			(interested,sleeping,ignored))

	def populate_treeview(self):
		model = self.controller.model
		tree = self.tree
		treestore = gtk.TreeStore(int,str,str,str)
		tree.set_model(treestore)

		column = gtk.TreeViewColumn('id')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, False)
		column.add_attribute(cell, "text", 0)

		column = gtk.TreeViewColumn('package')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, False)
		column.add_attribute(cell, "text", 1)
		column.set_sort_column_id(1)

		column = gtk.TreeViewColumn('severity')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell,False)
		column.add_attribute(cell, "text", 2)
		column.set_sort_column_id(2)
		treestore.set_sort_func(2, self.severity_sort_cb)

		column = gtk.TreeViewColumn('subject')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell,False)
		column.add_attribute(cell, "text", 3)

	def row_selected_cb(self,tree,path,column):
		treemodel = tree.get_model()
		row = treemodel[path[0]][0]
		os.system("sensible-browser http://bugs.debian.org/%s &" % row)

	def ignore_cb(self,button):
		offs,col = self.tree.get_cursor()
		if offs:
			num = self.tree.get_model()[offs[0]][0]
			self.controller.ignore_bug(num)

	def sleep_cb(self,button):
		offs,col = self.tree.get_cursor()
		if offs:
			num = self.tree.get_model()[offs[0]][0]
			self.controller.sleep_bug(num)
	
	def severity_sort_cb(self,treestore,iter1,iter2):
		a = treestore.get_value(iter1, 2)
		b = treestore.get_value(iter2, 2)
		av = debgtd.severities[a]
		bv = debgtd.severities[b]
		return av - bv

	def refresh_data_cb(self, button):
		user = self.wTree.get_widget("user_email").get_text()
		self.controller.set_user(user)
		self.controller.import_new_bugs()

	### listener methods for Model events

	def bug_added(self, bug):
		treestore = self.tree.get_model()
		self.wTree.get_widget("refresh_data_button").set_label("Update")
		if not bug.sleeping() and not bug.ignoring() and not bug.is_done():
			treestore.append(None, [bug['id'],
			bug['package'],
			bug['severity'],
			bug['subject']])
		self.update_summary_label()

	def bug_sleeping(self, bug):
		self.hide_bug(bug['id'])

	def bug_ignored(self, bug):
		self.hide_bug(bug['id'])
	
	def bug_changed(self, bug):
		if bug.sleeping() or bug.ignoring() or bug.is_done():
			self.hide_bug(bug['id'])

	def clear(self):
		treestore = self.tree.get_model()
		self.wTree.get_widget("refresh_data_button").set_label("Fetch")
		treestore.clear()
		# XXX: should clear the user too?

	### helper methods for model event listener callbacks 

	def hide_bug(self,bugnum):
		treemodel = self.tree.get_model()
		offs,col = self.tree.get_cursor()
		column = 0 # TODO: enumerate these somewhere
		# quick optimisation if the correct row is already selected
		if offs:
			iter = treemodel.get_iter(offs)
			rowid = treemodel.get_value(iter, column)
			if rowid == bugnum:
				treemodel.remove(iter)
				self.update_summary_label()
				return

		iter = treemodel.get_iter_first()
		rowid = bugnum + 1 # a fake value
		while rowid != bugnum:
			rowid = treemodel.get_value(iter, column)
			if rowid == bugnum:
				treemodel.remove(iter)
				break
			else:
				iter = treemodel.iter_next(iter)
				# the bug isn't being displayed at the moment anyway
				if not iter:
					break

		self.update_summary_label()

	def go(self):
		gtk.main()

	def user_changed(self, user):
		self.wTree.get_widget("user_email").set_text(user)
