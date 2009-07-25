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
import threading

import debgtd
from debgtd.controller import Controller

class TriageWindow:
	def __init__(self,controller,gladefile):
		self.controller = controller
		self.wTree = gtk.glade.XML(gladefile,"triage_window")
		window = self.wTree.get_widget("triage_window")
		window.resize(640,400)

		# signals
		window.connect("destroy", lambda x: self.close())
		self.wTree.get_widget("closebutton").connect("clicked",
			lambda x: self.close())
		self.wTree.get_widget("applybutton").connect("clicked",
			self.apply_button)
		self.wTree.get_widget("nextaction").connect("activate",
			self.apply_button)
		self.wTree.get_widget("sleepbutton").connect("clicked",
			self.sleep_button)
		self.wTree.get_widget("ignorebutton").connect("clicked",
			self.ignore_button)
		gtk.link_button_set_uri_hook(lambda x,y: self.current_bug and \
			os.system("sensible-browser http://bugs.debian.org/%s &" \
			% self.current_bug['id']))
		# initialisation
		self.processed = 0
		self.target = 0
		self.current_bug = None

	def open(self):
		window = self.wTree.get_widget("triage_window")
		self.get_next_bug()
		window.show()

	def close(self):
		self.processed = 0
		self.target    = 0
		window = self.wTree.get_widget("triage_window")
		if window:
			window.hide()

	def get_next_bug(self):
		bugs_todo = filter(lambda b: \
		not b.has_nextaction() and not b.ignoring() and not b.sleeping(),
			self.controller.model.bugs.values())
		if 0 < len(bugs_todo):
			self.current_bug = bugs_todo[0]
			if not self.target:
				self.target = len(bugs_todo)
		else:
			self.current_bug = None
			self.target = 0
		self.wTree.get_widget("nextaction").set_text('')
		self.update_currentbug()
		self.update_progress()

	def apply_button(self,button):
		text = self.wTree.get_widget("nextaction").get_text()
		self.controller.set_nextaction(self.current_bug['id'], text)
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
		package_label = self.wTree.get_widget("package_label")
		severity_label = self.wTree.get_widget("severity_label")
		subject_label = self.wTree.get_widget("subject_label")
		status_label = self.wTree.get_widget("status_label")
		if self.current_bug:
			if self.current_bug.is_done():
				status_label.set_label("done")
			else:
				status_label.set_label("?")
			subject_label.set_label(self.current_bug['subject'])
			package_label.set_label(self.current_bug['package'])
			severity_label.set_label(self.current_bug['severity'])
			subject_label.set_sensitive(True)
		else:
			package_label.set_label('there are no bugs to triage.')
			severity_label.set_label('')
			subject_label.set_sensitive(False)
			subject_label.set_label('')
			status_label.set_label('')

	def update_progress(self):
		progressbar = self.wTree.get_widget("progressbar")
		progresslabel = self.wTree.get_widget("progresslabel")
		progresslabel.set_text("%d / %d" % (self.processed, self.target))
		if 0 == self.target:
			progressbar.set_fraction( 1.0 )
		else:
			progressbar.set_fraction( float(self.processed) / float(self.target) )

class Gui:
	def __init__(self,controller):
		self.controller = controller
		self.active = True

		try:
			gtk.init_check()
		except RuntimeError, e:
			sys.exit('E: %s. Exiting.' % e)

		gtk.gdk.threads_init()

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
		self.wTree.get_widget("quit_menu_item").connect("activate", self.quit_cb)
		self.wTree.get_widget("window1").connect("destroy", self.quit_cb)

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
		button.set_sensitive(False)

		self.wTree.get_widget("user_email").connect("activate",
			self.user_changed_cb)

		self.tw = TriageWindow(self.controller,self.gladefile)

	def user_changed_cb(self,label):
		self.controller.set_user(label.get_text())

	def open_triage_window(self,button):
		self.tw.open()

	def toggle_triage_button(self):
		bugs_todo = filter(lambda b: \
			not b.has_nextaction() and not b.ignoring() and not b.sleeping(),
			self.controller.model.bugs.values())
		button = self.wTree.get_widget("triage_button")
		button.set_sensitive(len(bugs_todo) > 0)

	def update_summary_label(self):
		model = self.controller.model
		label = self.wTree.get_widget("num_bugs_label")

		total    = set(model.bugs)
		done     = set(filter(lambda x: model.bugs[x].is_done(), total))
		sleeping = set(filter(lambda x: model.bugs[x].sleeping(), total))
		ignoring = set(filter(lambda x: model.bugs[x].ignoring(), total))
		nextact  = set(filter(lambda x: model.bugs[x].has_nextaction(), total))

		displaying = nextact - ignoring
		to_triage  = total - ignoring - nextact - sleeping

		label.set_text("displaying %d bugs, %d to triage " \
			"(%d sleeping; %d ignored; %d done; %d total)" % \
			(len(displaying), len(to_triage),
			# XXX: the following aren't really of interest to the end-user
			len(sleeping), len(ignoring), len(done), len(total)))

	def populate_treeview(self):
		model = self.controller.model
		tree = self.tree
		treestore = gtk.TreeStore(int,str,str,str,str)
		tree.set_model(treestore)

		column = gtk.TreeViewColumn('id')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, False)
		column.add_attribute(cell, "text", 0)
		column.set_sort_column_id(0)

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

		column = gtk.TreeViewColumn('next-action')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell,False)
		column.add_attribute(cell, "text", 3)
		column.set_sort_column_id(3)

		column = gtk.TreeViewColumn('subject')
		tree.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell,False)
		column.add_attribute(cell, "text", 4)

	def row_selected_cb(self,tree,path,column):
		treemodel = tree.get_model()
		row = treemodel[path[0]][0]
		os.system("sensible-browser http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=%s &" % row)

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
		widgets = ("refresh_data_button", "sleep_bug_button",
			"ignore_bug_button", "user_email", "sleep_menu_item",
			"ignore_menu_item", "quit_menu_item")
		for widget in widgets:
			self.wTree.get_widget(widget).set_sensitive(False)

		old_label = button.get_label()
		button.set_label("Updating...")

		def refresh_worker():
			user = self.wTree.get_widget("user_email").get_text()
			self.controller.set_user(user)
			self.controller.import_new_bugs()
			if not self.active:
				return
			for widget in widgets:
				self.wTree.get_widget(widget).set_sensitive(True)
			button.set_label(old_label)
		threading.Thread(target=refresh_worker).start()

	### listener methods for Model events

	def bug_added(self, bug):
		treestore = self.tree.get_model()
		self.wTree.get_widget("refresh_data_button").set_label("Update")
		if not bug.sleeping() and not bug.ignoring() and \
			bug.has_nextaction():
			treestore.append(None, [bug['id'],
			bug['package'],
			bug['severity'],
			bug.get_nextaction(),
			bug['subject']])
		self.update_summary_label()
		self.toggle_triage_button()

	def bug_sleeping(self, bug):
		self.hide_bug(bug['id'])
		self.toggle_triage_button()

	def bug_ignored(self, bug):
		self.hide_bug(bug['id'])
		self.toggle_triage_button()
	
	def bug_changed(self, bug):
		if not self.active:
			return
		if bug.sleeping() or bug.ignoring() or bug.is_done():
			self.hide_bug(bug['id'])
			self.toggle_triage_button()
		# XXX: hacky. remove the bug and add it again to update treeview
		else:
			self.hide_bug(bug['id'])
			self.bug_added(bug)

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
		while iter and rowid != bugnum:
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

	def quit_cb(self, *_):
		self.active = False
		gtk.main_quit()
