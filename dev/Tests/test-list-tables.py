#!/usr/bin/env python
# encoding: utf-8

from pyo import *

s = Server().boot()

dump = NewTable(length=3, chnls=3)
list = [NewTable(length=3, chnls=3) for i in range(2)]

source1 = Sine(300, mul=.1).out()
source2 = Sine(400, mul=.1).out()
source3 = Sine(500, mul=.1).out()

obj = [source1,source2,source3]

rec = TableRec(input=obj, table=dump)
readt = TableRead(dump, freq=dump.getRate())

cpt = -1

def record():
    global cpt
    cpt += 1
    if cpt < len(list):
        rec.setTable(list[cpt])
        rec.play()
        
def read(index):
    source1.stop()
    source2.stop()
    source3.stop()
    readt.setTable(list[index])
    readt.out()

def plus():
    source1.freq += 100
    source2.freq += 100
    source3.freq += 100
    source1.out()
    source2.out()
    source3.out()
    
    
#S�quence � suivre pour reproduire le probl�me
#1. lancer record() une fois
#2. lancer read(0) pour entendre la premi�re piste
#2. lancer plus() pour pour pouvoir distinguer les pistes
#3. lancer record() une seconde fois
#4. lancer read(1) pour entendre ce qui vient d'�tre enregistr�.
#   cette �tape devrait fonctionner sans probl�me...
#5. lancer read(0) pour entendre la premi�re piste � nouveau.
#   le programme plante...

s.start()
s.gui(locals())