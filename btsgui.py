#!/usr/bin/python

#  jon's hacky bts helper


import sys
import gtk
import gtk.glade
import os

from bts import Model, Controller

class GUI:
	def __init__(self,model,controller):
		self.model = model
		self.controller = controller
		self.gladefile = "bts.glade"
		self.wTree = gtk.glade.XML(self.gladefile,"window1")

		window = self.wTree.get_widget("window1")
		window.show()
		self.wTree.get_widget("window1").connect("destroy", gtk.main_quit)

		self.tree = self.wTree.get_widget("treeview1")
		self.tree.connect("row-activated", self.row_selected_cb)
		self.populate_treeview()

		label = self.wTree.get_widget("num_bugs_label")
		label.set_text("%d bugs" % len(self.model.bugs))

	def populate_treeview(self):
		self.controller.load_from_file("data.txt")
		model = self.model = controller.model
		tree = self.tree
		treestore = gtk.TreeStore(int,str)
		tree.set_model(treestore)

		column = gtk.TreeViewColumn('id')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, False)
		column.add_attribute(cell, "text", 0)

		column = gtk.TreeViewColumn('subject')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell,False)
		column.add_attribute(cell, "text", 1)

		for key in model.bugs:
			treestore.append(None, [ key, model.bugs[key]['subject'] ])

	def row_selected_cb(self,tree,path,column):
		treemodel = tree.get_model()
		row = treemodel[path[0]][0]
		os.system("x-www-browser http://bugs.debian.org/%s" % row)

if __name__ == "__main__":
	model = Model()
	controller = Controller(model)
	gui = GUI(model,controller) # XXX: only controller soon?
	gtk.main()
