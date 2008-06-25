#!/usr/bin/python
import sys
import os
from os import environ
from sys import exit,stderr
import SOAPpy

if not environ.has_key("DEBEMAIL"):
	stderr.write("error: please define DEBEMAIL.\n")
	exit(1)

user = environ['DEBEMAIL']

# this is out-of-date, but it's the data returned for this
# tag which is causing the problems
tracking = "needs-attention"
url = 'http://bugs.debian.org/cgi-bin/soap.cgi'
namespace = 'Debbugs/SOAP'
if os.environ.has_key("http_proxy"):
	my_http_proxy=os.environ["http_proxy"].replace("http://","")
else:
	my_http_proxy=None

server = SOAPpy.SOAPProxy(url, namespace,http_proxy=my_http_proxy)

usertags  = server.get_usertag(user)._asdict()
if not usertags.has_key(tracking):
	sys.exit(1)

# wrapped up in a soap:map for some reason
foo = server.get_status(usertags[tracking])
foo2 = foo._aslist()[0]
# foo2 is now a list of items, one per requested bug

# if we only requested one bug, irrespective of whether it was in
# an array in the soap request, the response will be unboxed.
if len(usertags[tracking]) == 1:
    print "reboxing the thingummy"
    foo2 = { 'value': foo2[1] }

hash = {}
for item in foo2:
    # each 'item' returned is a two-element hash, keys 'key' and 'value'
    item2 = item._asdict()['value']
    hash[item2['id']] = item2._asdict()

print hash.keys()
