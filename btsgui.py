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

import bts
from bts import Model, Controller

class GUI:
	def __init__(self,controller):
		self.controller = controller

		if os.path.isfile("bts.glade"):
			self.gladefile = "bts.glade"
		elif os.path.isfile("/usr/local/share/debgtd/bts.glade"):
			self.gladefile = "/usr/local/share/debgtd/bts.glade"
		else:
			self.gladefile = "/usr/share/debgtd/bts.glade"

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
		button = self.wTree.get_widget("refresh_data_button")
		button.connect("clicked", self.refresh_data_cb)

		button = self.wTree.get_widget("ignore_bug_button")
		button.connect("clicked", self.ignore_cb)

		self.wTree.get_widget("user_email").set_text("jon+bts@alcopop.org")

	# XXX: we shouldn't prod the bug this internally, instead rely on a
	# model method (or some chain of filter rules for what to display)
	# TODO: not taking into account that we filter out done bugs below
	def update_summary_label(self):
		model = self.controller.model
		label = self.wTree.get_widget("num_bugs_label")

		total = len(filter(lambda bug: '' == bug['done'], model.bugs.values()))
		# XXX BUG there might be an intersection between these
		# should use real set logic instead of arithmetic
		sleeping = len(model.get_sleeping_bugs())
		ignored = len(model.get_ignored_bugs())
		interested = total - sleeping - ignored

		label.set_text("%d bugs (%d sleeping; %d ignored)" % \
			(interested,sleeping,ignored))

	def populate_treeview(self):
		model = controller.model
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
		os.system("x-www-browser http://bugs.debian.org/%s" % row)

	def ignore_cb(self,button):
		offs,col = self.tree.get_cursor()
		num = self.tree.get_model()[offs[0]][0]
		self.controller.ignore_bug(num)

	def sleep_cb(self,button):
		offs,col = self.tree.get_cursor()
		num = self.tree.get_model()[offs[0]][0]
		self.controller.sleep_bug(num)
	
	def severity_sort_cb(self,treestore,iter1,iter2):
		a = treestore.get_value(iter1, 2)
		b = treestore.get_value(iter2, 2)
		av = bts.severities[a]
		bv = bts.severities[b]
		return av - bv

	def refresh_data_cb(self, button):
		model = self.controller.model
		user  = self.wTree.get_widget("user_email").get_text()
		if not model:
			controller = self.controller
			controller.model = Model(user)
			controller.model.add_listener(self)
			controller.import_new_bugs()
		else:
			# XXX handle me
			self.controller.import_new_bugs()

	### listener methods for Model events

	def bug_added(self, bug):
		# XXX: we shouldn't prod the bug this internally, instead
		# rely on a model method (or some chain of filter rules
		# for what to display)
		treestore = self.tree.get_model()
		if not bts.sleeping in bug['debgtd'] \
		and not bts.ignoring in bug['debgtd'] \
		and '' == bug['done']:
			treestore.append(None, [bug['id'],
			bug['package'],
			bug['severity'],
			bug['subject']])
		self.update_summary_label()

	def bug_sleeping(self, bug):
		self.hide_bug(bug)

	def bug_ignored(self, bug):
		self.hide_bug(bug)

	### helper methods for model event listener callbacks 

	def hide_bug(self,bug):
		treemodel = self.tree.get_model()
		if not treemodel:
			print "hide_bug: wtf, no treemodel?!"
			return
		offs,col = self.tree.get_cursor()
		if not offs:
			print "hide_bug: wtf, no offs?!"
			return
		row = self.tree.get_model()[offs[0]][0]
		iter = treemodel.get_iter(offs)
		# TODO: this only works if the callstack is guaranteed to be
		# self.ignore_cb -> ... -> self.bug_ignored: i.e., if at some
		# point an external influence could ignore a bug, we will
		# need to iterate.
		treemodel.remove(iter)
		self.update_summary_label()

	def go(self):
		gtk.main()


if __name__ == "__main__":
	controller = Controller()
	gui = GUI(controller)
	controller.add_view(gui)
	controller.go()
	print "exiting..."
	controller.save_to_file()
