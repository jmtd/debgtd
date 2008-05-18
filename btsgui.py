#!/usr/bin/python

#  jon's hacky bts helper


import sys
import gtk
import gtk.glade

from bts import BtsModel

class BtsGUI:
	def __init__(self,model):
		self.model = model
		self.gladefile = "bts.glade"
		self.wTree = gtk.glade.XML(self.gladefile,"window1")

		window = self.wTree.get_widget("window1")
		window.show()
		self.wTree.get_widget("window1").connect("destroy", gtk.main_quit)

		self.tree = self.wTree.get_widget("treeview1")
		self.populate_treeview()

	def populate_treeview(self):
		model = self.model
		tree = self.tree
		treestore = gtk.TreeStore(int)
		column = gtk.TreeViewColumn('bug number')
		tree.set_model(treestore)
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, False)
		column.add_attribute(cell, "text", 0)
		for bug in model.usertags['needs-attention']:
			treestore.append(None, [ bug ])

if __name__ == "__main__":
	model = BtsModel()
	gui = BtsGUI(model)
	gtk.main()
