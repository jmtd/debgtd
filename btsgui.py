#!/usr/bin/python

#  jon's hacky bts helper


import sys
import gtk
import gtk.glade
import os

import bts
from bts import Model, Controller

class GUI:
	def __init__(self,model,controller):
		self.model = model
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
		button = self.wTree.get_widget("sleep_bug_button")
		button.connect("clicked", self.sleep_cb)

		self.populate_treeview()
		self.model_changed()

	def populate_treeview(self):
		self.controller.load_from_file("data.txt")
		model = self.model = controller.model
		tree = self.tree
		treestore = gtk.TreeStore(int,str,str)
		tree.set_model(treestore)

		column = gtk.TreeViewColumn('id')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, False)
		column.add_attribute(cell, "text", 0)

		column = gtk.TreeViewColumn('severity')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell,False)
		column.add_attribute(cell, "text", 1)
		column.set_sort_column_id(1)
		treestore.set_sort_func(1, self.severity_sort_cb)

		column = gtk.TreeViewColumn('subject')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell,False)
		column.add_attribute(cell, "text", 2)

	def row_selected_cb(self,tree,path,column):
		treemodel = tree.get_model()
		row = treemodel[path[0]][0]
		os.system("x-www-browser http://bugs.debian.org/%s" % row)

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
	
	def severity_sort_cb(self,treestore,iter1,iter2):
		a = treestore.get_value(iter1, 1)
		b = treestore.get_value(iter2, 1)
		av = bts.severities[a]
		bv = bts.severities[b]
		return av - bv

	def model_changed(self):
		print "handling a model change"
		treestore = self.tree.get_model()
		model = self.controller.model
		treestore.clear()
		print "debug: %d\n" % len(model.bugs)
		for key in model.bugs:
			bug = model.bugs[key]
			treestore.append(None, [key, bug['severity'], bug['subject']])
		label = self.wTree.get_widget("num_bugs_label")
		label.set_text("%d bugs" % len(self.model.bugs))

if __name__ == "__main__":
	model = Model()
	controller = Controller(model)
	gui = GUI(model,controller) # XXX: only controller soon?
	controller.add_listener(gui)
	gtk.main()
	print "exiting..."
	controller.save_to_file("data.txt")
