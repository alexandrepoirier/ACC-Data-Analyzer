#!/usr/bin/env python
# encoding: utf-8
from pyo import *
import ioIndexes
from classeBeatGen import BeatGen
import random

MY_SNDS = "/Volumes/DOCUMENTS/UdeM/_Automne 2013/Creation musicale en langage python/Devoir 3/sons/"

s = Server(sr=48000, nchnls=2, buffersize=256, duplex=1)
s.setOutputDevice(ioIndexes.getOutput('Scarlett'))
s.boot()
s.amp = .5

def changeTranspo():
    f1 = random.randint(25, 100)
    f2 = random.randint(25, 100)
    f3 = random.randint(25, 100)
    f4 = random.randint(25, 100)
    beat1.setTranspo(f1/100.)
    beat2.setTranspo(f2/100.)
    beat3.setTranspo(f3/100.)
    beat4.setTranspo(f4/100.)

##Reception OSC
osc = OscReceive(port=10001, address=['/rgh','/mag','/act','/accx','/accy','/accz'])
accx = Scale(osc['/accx'], inmin=-90, inmax=90, outmin=0, outmax=1)
accy = Scale(osc['/accy'], inmin=-90, inmax=90, outmin=0, outmax=1)
accz = Scale(osc['/accz'], inmin=-90, inmax=90, outmin=0, outmax=1)

thresh = Thresh(osc['/mag'], threshold=3)
trigfunc = TrigFunc(thresh, changeTranspo)

beat1 = BeatGen(MY_SNDS + "ice1.wav", time=.125, poly=4, type=1, bal=.2).play()
beat2 = BeatGen(MY_SNDS + "ice2.wav", time=(.125*4/3.), poly=3, type=3).play()
beat3 = BeatGen(MY_SNDS + "ice3.wav", time=.125, taps=4, poly=2, type=2, env="soft", mul=accx).play()
beat4 = BeatGen(MY_SNDS + "ice4.wav", time=1, taps=4, poly=2, type=1, env="soft", bal=.2, mul=accy).play()

#Disto et EQ sur beat3
disto = Disto(beat3.use(), drive=.988, slope=.9, mul=.03)
eq = EQ(disto, freq=110, q=1.3, boost=11, type=1)

# Les quatre generateurs de rythmes passent dans une reverb et sortent aux hautparleurs
verb = Freeverb(beat1.use()+beat2.use()+eq+beat4.use(),
                size=.88, damp=.53, bal=.6, mul=1).mix(2).out()
                
s.gui()