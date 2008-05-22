#!/usr/bin/python
from bts import Model, Controller
from pickle import dump
from os import environ
from sys import exit,stderr

if not environ.has_key("DEBEMAIL"):
	stderr.write("error: please define DEBEMAIL.\n")
	exit(1)

model = Model(environ["DEBEMAIL"])
controller = Controller(model)
path = "data.txt"
controller.reload()
#controller.load_from_file(path)
model = controller.model
fp = open(path,"w")
dump(model,fp)
fp.close()
