#!/usr/bin/python
from bts import Model, Controller
from pickle import dump
model = Model()
controller = Controller(model)
path = "data.txt"
controller.reload()
#controller.load_from_file(path)
model = controller.model
print model
print type(model.usertags)
print "usertags:"
print model.usertags
print "submitted:"
print model.submitted
fp = open(path,"w")
dump(model,fp)
fp.close()

# XXX: the array isn't being dumped :(
