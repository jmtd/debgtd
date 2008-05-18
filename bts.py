#!/usr/bin/python
# see http://wiki.debian.org/DebbugsSoapInterface

import SOAPpy

class BtsModel:
	def __init__(self):
		self.path = "/home/jon/wd/mine/bts/data.txt"

		self.url = 'http://bugs.debian.org/cgi-bin/soap.cgi'
		self.namespace = 'Debbugs/SOAP'
		self.user = "jon+bts@alcopop.org"

		self.server = SOAPpy.SOAPProxy(self.url, self.namespace)

		self.submitted = self.server.get_bugs("submitter", self.user)
		print "debug: submitted = %d\n" % len(self.submitted)
		self.usertags  = self.server.get_usertag(self.user)._asdict()
		print "debug: usertags  = %d\n" % len(self.usertags)
		print self.usertags

		# are there any bugs in the first set not dealt with yet?
		# XXX can't flesh this bit out until something matches the
		# criteria :-)
		subm = set(self.submitted)
		already = set()
		for key in self.usertags.keys():
			already |= set(self.usertags[key])
		for bug in subm - already:
			print "bug %d undealt with" % bug
