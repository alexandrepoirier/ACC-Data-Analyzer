#!/usr/bin/env python
# encoding: utf-8
from pyo import *

s = Server(sr=48000, nchnls=2, buffersize=256, duplex=1).boot()

osc = OscReceive(port=10001, address=['/rgh','/mag','/act','/accx','/accy','/accz'])

printx = Print(osc['/accx'], interval=1, message="ACC-X")
printy = Print(osc['/accy'], interval=1, message="ACC-Y")
printz = Print(osc['/accz'], interval=1, message="ACC-Z")

printrgh = Print(osc['/rgh'], interval=1, message="ACC-RGH")
printmag = Print(osc['/mag'], interval=1, message="ACC-MAG")
printact = Print(osc['/act'], interval=1, message="ACC-ACT")

s.gui(locals())