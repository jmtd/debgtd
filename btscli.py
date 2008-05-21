#!/usr/bin/python
from bts import Model, Controller
from pickle import dump
model = Model()
controller = Controller(model)
path = "data.txt"
controller.reload()
#controller.load_from_file(path)
model = controller.model
fp = open(path,"w")
dump(model,fp)
fp.close()
