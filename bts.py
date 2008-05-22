#!/usr/bin/python
# see http://wiki.debian.org/DebbugsSoapInterface

import SOAPpy
import os
from pickle import load, dump

class Model:
	def __init__(self):
		self.user = "jon+bts@alcopop.org"
		self.usertags = {}
		self.bugs = {}

class Controller:
	def __init__(self,model):

		self.url = 'http://bugs.debian.org/cgi-bin/soap.cgi'
		self.namespace = 'Debbugs/SOAP'

		self.model = model

		if os.environ.has_key("http_proxy"):
			my_http_proxy=os.environ["http_proxy"].replace("http://","")
		else:
			my_http_proxy=None

		self.server = SOAPpy.SOAPProxy(self.url, self.namespace,
			http_proxy=my_http_proxy)
		self.needswrite = False

	def load_from_file(self,file):
		fp = open(file,"r")
		self.model = load(fp)
		fp.close()
		self.needswrite = False

	def save_to_file(self,file,force=False):
		if not force and self.needswrite:
			fp = open(file,"w")
			dump(self.model,fp)
			fp.close()
			self.needswrite = False

	def reload(self):
		model = self.model
		model.usertags  = self.server.get_usertag(model.user)._asdict()

		# import the ones of interest
		if model.usertags.has_key("needs-attention"):
			foo = self.server.get_status(model.usertags['needs-attention'])
			for item in foo[0]:
				model.bugs[item[1]['id']] = item[1]._asdict()

	# we don't want to track this bug anymore. tag it 'debstd.sleeping'
	# XXX: we may need to shell-escape the model.user string
	def sleep_bug(self,bug):
		os.system("DEBEMAIL=\"%s\" bts usertag %d debstd.sleeping" %
			(self.model.user, bug))
		del self.model.bugs[bug]
		self.needswrite = True
