#!/usr/bin/env python
# encoding: utf-8
from pyo import *

########################################
### Definition de ma classe Beat Gen ###
########################################
class BeatGen:
    def __init__(self, path, time=.125, taps=16, poly=2, type=1, env="hard", transpo=1., bal=0, mul=1):
        #################################
        ### Declaration des variables ###
        #################################
        self.sound = SndTable(path)
        self.time = Sig(time)
        self.transpo = Sig(transpo)
        self.bal = Sig(bal)
        self.mul = Sig(mul)
        self.fadein = Linseg([(0,0),(4,1)])
        self.fadeout = Linseg([(0,1),(4,0)])
        
        # Le type permet de decider quelle partie de temps accentuer
        ### 1 = les temps forts; 2 = les contre-temps; 3 = les temps plus faibles
        if(type == 1):
            self.trigger = Beat(time=self.time, taps=taps, w1=90, w2=50, w3=30, poly=poly)
        elif(type == 2):
            self.trigger = Beat(time=self.time, taps=taps, w1=50, w2=90, w3=30, poly=poly)
        elif(type == 3):
            self.trigger = Beat(time=self.time, taps=taps, w1=30, w2=50, w3=90, poly=poly)
            

        if(env == "soft"):
            self.adsr = HannTable()
        elif(env == "hard"):
            self.adsr = LinTable([(0,0),(150,1),(1000,.25),(8191,0)])
            
        # Generateur des 'grains'
        self.env = TrigEnv(self.trigger, self.adsr, dur=self.trigger["dur"], mul=self.trigger["amp"])
        self.osc = OscTrig(self.sound, self.trigger, freq=self.transpo/self.sound.getDur(), mul=self.env)
        
        # Effet de Delay/flanger
        ### Le sinus oscille entre .005 et .015
        self.lfo = Sine(freq=.1, mul=.01, add=.01)
        self.delay = Delay(self.osc, delay=self.lfo, feedback=.7)
        
        self.sortie = Selector(inputs=[self.osc,self.delay], voice=self.bal, mul=self.mul)
        
    ################################
    ### Declaration des methodes ###
    ################################
    def out(self):
        """ Sortie aux hautparleurs """
        self.sortie.out()
        return self
        
    def use(self):
        """ Permet d'utiliser l'objet audio dans une chaine """
        return self.sortie
        
    def play(self):
        """ Demarre le trigger et fait un fadein sur le volume """
        self.mul.value = self.fadein.play()*self.mul.value
        self.trigger.play()
        return self
        
    def stop(self):
        self.trigger.stop()
        
    def fadeOut(self):
        self.mul.value = self.fadeout.play()*self.mul.value
        
    def newBeat(self):
        self.trigger.new()
        
    def setTime(self, x):
        self.time.value = x
        
    def setTranspo(self, x):
        self.transpo.value = x
        
    def setBal(self, x):
        self.sortie.setVoice(x)
        
    def setMul(self, x):
        self.mul.value = x