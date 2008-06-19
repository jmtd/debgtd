#!/usr/bin/python
from os import environ
from sys import exit,stderr
import SOAPpy

if not environ.has_key("DEBEMAIL"):
	stderr.write("error: please define DEBEMAIL.\n")
	exit(1)

user = environ['DEBEMAIL']

tracking = "needs-attention"
url = 'http://bugs.debian.org/cgi-bin/soap.cgi'
namespace = 'Debbugs/SOAP'
server = SOAPpy.SOAPProxy(url, namespace)


usertags  = server.get_usertag(user)._asdict()
if not usertags.has_key(tracking):
	sys.exit(1)

foo = server.get_status(usertags[tracking])

hash = {}
foo2 = foo._aslist()
foo3 = foo2[0]
print foo3
print "ZOMG"
print foo3._aslist()
for item in foo3:
    if int == type(item):
        print "bah, int: %d"%item
    else:
        item2 = item._asdict()['value']
        hash[item2['id']] = item2._asdict()
