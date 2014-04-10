#!/usr/bin/env python
# encoding: utf-8
from pyo import *
from random import uniform

class Synth:
    def __init__(self):
        self.note = OscReceive(port=9000, address=['/mrmr/accelerometerX/1/iPhone-Alex','/mrmr/accelerometerZ/1/iPhone-Alex','/mrmr/accelerometer/force/3/iPhone-Alex','/mrmr/accelerometer/force/2/iPhone-Alex',
        '/mrmr/accelerometerY/1/iPhone-Alex','/mrmr/accelerometer/angle/3/iPhone-Alex','/mrmr/accelerometer/direction/2/iPhone-Alex'])
        self.pit=self.note['/mrmr/accelerometerX/1/iPhone-Alex']
       
        self.amp = MidiAdsr(self.note['/mrmr/accelerometerY/1/iPhone-Alex'], attack=0.001, 
                            decay=.1, sustain=.7, release=1, mul=.3)
        self.var=self.note['/mrmr/accelerometerZ/1/iPhone-Alex']
        self.var2=self.note['/mrmr/accelerometer/force/3/iPhone-Alex']
        self.var3=self.note['/mrmr/accelerometer/force/2/iPhone-Alex']
        #self.pit=midiToHz(self.pi)
        
        self.osc1 = LFO(freq=self.pit*2, sharp=0.25, mul=self.amp).mix(1)
        self.osc2 = LFO(freq=self.pit*2*1.5*0.997, sharp=0.25, mul=self.var*2).mix(1)
        self.osc3 = LFO(freq=self.pit*8*1.25, sharp=0.25, mul=self.var2*4).mix(1)
        self.osc4 = LFO(freq=self.pit*16*1.875*1.009, sharp=0.25, mul=self.var3*8).mix(1)

        # Mix stereo (osc1 et osc3 a gauche, osc2 et osc4 a droite)
        self.mix = Mix([self.osc1+self.osc3, self.osc2+self.osc4], voices=2)

        # Distortion avec LFO sur le drive
        self.lfo = Sine(freq=self.note['/mrmr/accelerometer/direction/2/iPhone-Alex']*0.5, mul=0.45, add=0.5)
        self.disto = Disto(self.mix, drive=self.lfo, slope=0.95, mul=.2)

    def out(self):
        self.disto.out()
        return self

    def sig(self):
        return self.disto


s = Server().boot() 



# roue de modulation = amplitude du vibrato
#ctl = Midictl(1, minscale=0, maxscale=.2)
#bend = Bendin(brange=2, scale=1) # Pitch bend
#lf = Sine(freq=5, mul=ctl, add=1) # Vibrato
a1 = Synth()
lct=a1.note['/mrmr/accelerometer/angle/3/iPhone-Alex']

comp = Compress(a1.sig(), thresh=-20, ratio=6)
dly=Delay(comp.mix(2), delay=[.15,.2], feedback=lct/10, mul=.2)
rev = WGVerb(dly.mix(2), feedback=.8, cutoff=10000, bal=.3).out().mix(2)

s.gui(locals())