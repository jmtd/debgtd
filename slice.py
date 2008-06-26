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

#tracking = "needs-attention"
tracking = "debgtd.tracking"

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
foo = server.get_status(usertags[tracking])[0]

hash = {}
# if we only requested one bug, irrespective of whether it was in
# an array in the soap request, the response will be unboxed.
if 1 == len(usertags[tracking]):
    foo = foo['value']
    hash[foo['id']] = foo._asdict()
else:
    for item in foo:
        # each 'item' returned is a two-element hash, keys 'key' and 'value'
        item2 = item['value']
        hash[item2['id']] = item2._asdict()

print hash.keys()
