#!/usr/bin/env python
# encoding: utf-8
from pyo import *
import ioIndexes

s = Server(sr=48000, nchnls=2, buffersize=256, duplex=1)
s.setOutputDevice(ioIndexes.getOutput('Scarlett'))
s.boot()
s.amp = .5

##Reception OSC
osc = OscReceive(port=10001, address=['/rgh','/mag','/act','/accx','/accy','/accz'])
accx = Scale(osc['/accx'], inmin=-90, inmax=90, outmin=0, outmax=1)
accy = Scale(osc['/accy'], inmin=-90, inmax=90, outmin=0, outmax=1)
accz = Scale(osc['/accz'], inmin=-90, inmax=90, outmin=0, outmax=1)

##On change de root quand le mouvement est large
thresh = Thresh(osc['/mag'], threshold=3)
root = TrigChoice(thresh, [49,55,61.7,73.42], init=32.7)

##Roughness et activity sont additionnés aux fréquences fondamentales
freqs1 = Sig(osc['/rgh'], mul=[1,1])
freqs2 = Sig(osc['/act'], mul=[1,1])

##Oscillateurs
sineL = SineLoop(freq=[(root*5)+freqs1,(root*7)-freqs1], feedback=.4*accx, mul=.2*accz)
saw = SuperSaw(freq=[(root*2)+freqs2,(root*3)-freqs2], mul=.2*accy)
sub = LFO(freq=root+freqs2, sharp=.37, type=0, mul=.2*accz)

##Mix de oscillateurs
mix = Mix([sineL,saw], voices=2)

##application de FreqShift sur le signal original
shift_val = Sig(osc['/mag'])
shift = FreqShift(mix, shift=5+shift_val, mul=.4)

##Delay et reverb sur le signal original
delayL = Delay(mix[0], delay=.01+accy, feedback=.2)
delayR = Delay(mix[1], delay=.01+accz, feedback=.2)
reverb = Freeverb([delayL, delayR], size=.65, damp=.29, bal=.62)

master = SigTo(value=1, time=3, init=0)
final_out = Mix(sub+shift+reverb, voices=2, mul=master).out()

s.gui()
