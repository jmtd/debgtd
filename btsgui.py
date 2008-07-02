#!/usr/bin/python

#  jon's hacky bts helper


import sys
import gtk
import gtk.glade
import os

import bts
from bts import Model, Controller

class GUI:
	def __init__(self,controller):
		self.controller = controller
		self.gladefile = "bts.glade"
		self.wTree = gtk.glade.XML(self.gladefile,"window1")

		window = self.wTree.get_widget("window1")
		window.resize(800,600)
		window.show()
		self.wTree.get_widget("quit_menu_item").connect("activate", gtk.main_quit)
		self.wTree.get_widget("window1").connect("destroy", gtk.main_quit)

		self.tree = self.wTree.get_widget("treeview1")
		self.tree.connect("row-activated", self.row_selected_cb)
		self.populate_treeview()

		self.update_summary_label()

		button = self.wTree.get_widget("sleep_bug_button")
		button.connect("clicked", self.sleep_cb)
		button = self.wTree.get_widget("refresh_data_button")
		button.connect("clicked", self.refresh_data_cb)

		button = self.wTree.get_widget("ignore_bug_button")
		button.connect("clicked", self.ignore_cb)

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

		for bug in model.bugs.values():
			# xxx: we shouldn't prod the bug this internally, instead
			# rely on a model method (or some chain of filter rules
			# for what to display)
			if not bts.sleeping in bug['debgtd'] \
			and not bts.ignoring in bug['debgtd'] \
			and '' == bug['done']:
				treestore.append(none, [bug['id'],
				bug['package'],
				bug['severity'],
				bug['subject']])

	def row_selected_cb(self,tree,path,column):
		treemodel = tree.get_model()
		row = treemodel[path[0]][0]
		os.system("x-www-browser http://bugs.debian.org/%s" % row)

	def ignore_cb(self,button):
		treemodel = self.tree.get_model()
		offs,col = self.tree.get_cursor()
		row = self.tree.get_model()[offs[0]][0]
		iter = treemodel.get_iter(offs)
		self.controller.ignore_bug(row)
		# TODO: the following should be moved to an event handler for
		# "model.bug changed". we need to implement events for that
		# get an iter. somehow.
		treemodel.remove(iter)
		self.update_summary_label()

	def sleep_cb(self,button):
		treemodel = self.tree.get_model()
		offs,col = self.tree.get_cursor()
		row = self.tree.get_model()[offs[0]][0]
		iter = treemodel.get_iter(offs)
		self.controller.sleep_bug(row)
		# TODO: the following should be moved to an event handler for
		# "model.bug changed". we need to implement events for that
		# get an iter. somehow.
		treemodel.remove(iter)
		self.update_summary_label()
	
	def severity_sort_cb(self,treestore,iter1,iter2):
		a = treestore.get_value(iter1, 2)
		b = treestore.get_value(iter2, 2)
		av = bts.severities[a]
		bv = bts.severities[b]
		return av - bv

	def refresh_data_cb(self, button):
		self.controller.import_new_bugs()

	### listener methods for Model events

	def bug_changed(self, bug):
		# aw, christ.
		print "should handle %d changing, but aren't." % bug

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

if __name__ == "__main__":
	if not os.environ.has_key("DEBEMAIL"):
		sys.stderr.write("error: please define DEBEMAIL.\n")
		sys.exit(1)
	model = Model(os.environ["DEBEMAIL"])
	controller = Controller(model)
	if os.path.isfile("data.txt"):
		controller.load_from_file("data.txt")
	gui = GUI(controller)
	controller.model.add_listener(gui)
	gtk.main()
	print "exiting..."
	controller.save_to_file("data.txt")
