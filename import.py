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
