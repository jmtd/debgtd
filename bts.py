#!/usr/bin/python
# see http://wiki.debian.org/DebbugsSoapInterface

import SOAPpy
from pickle import load

class Model:
	def __init__(self):
		self.user = "jon+bts@alcopop.org"
		self.submitted = {}
		self.usertags = {}

class Controller:
	def __init__(self,model):

		self.url = 'http://bugs.debian.org/cgi-bin/soap.cgi'
		self.namespace = 'Debbugs/SOAP'

		self.model = model

		self.server = SOAPpy.SOAPProxy(self.url, self.namespace)

	def load_from_file(self,file):
		fp = open(file,"r")
		self.model = load(fp)
		fp.close()

	def reload(self):
		model = self.model
		tmp = self.server.get_bugs("submitter", model.user)._aslist()
		#model.submitted = tmp._aslist()

		# now unpack 'em somehow
		foo = self.server.get_status(tmp)
		# foo is a hash, foo[0] the results, (key 'item')
		# foo[0] is a list
		# each element is another soapy thing, k/v
		# foo[0][x][1] is the stuff to save
		for item in foo[0]:
			model.submitted[item[1]['id']] = item[1]._asdict()

		model.usertags  = self.server.get_usertag(model.user)._asdict()
		print "debug: usertags  = %d\n" % len(model.usertags)
		print model.usertags

	# this method should probably be part of reload. it will look at the
	# configured 
	def refresh(self):
		"""this method should probably be part of reload. it will
		see which bugs have been introduced to our sources which we
		aren't tracking yet; also which bugs we are tracking that
		are not needs-attention and might have timed out (and thus
		be needs-attention); or have had activity."""
		# are there any bugs in the first set not dealt with yet?
		# XXX can't flesh this bit out until something matches the
		# criteria :-)
		subm = set(self.model.submitted)
		already = set()
		for key in self.model.usertags.keys():
			already |= set(model.usertags[key])
		for bug in subm - already:
			print "bug %d undealt with" % bug
