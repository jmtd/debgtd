#!/usr/bin/python
import os
from bts import Model, Controller
from pickle import dump
from os import environ
from os.path import isfile
from sys import exit,stderr

if not environ.has_key("DEBEMAIL"):
	stderr.write("error: please define DEBEMAIL.\n")
	exit(1)

model = Model(environ["DEBEMAIL"])
controller = Controller(model)
path = "data.txt"
if isfile(path):
    controller.load_from_file(path)

controller.import_new_bugs()

# save the results
model = controller.model
fp = open(path,"w")
dump(model.serialize(),fp)
fp.close()
