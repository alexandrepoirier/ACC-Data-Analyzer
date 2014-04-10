#!/usr/bin/env python
# encoding: utf-8

from math import degrees, pi, atan2
from pyo import OscReceive, OscListReceive, Scale, Metro, TrigFunc, TrigTableRec, NewTable, Percent

BUFFER_SIZE = 256
SAMP_RATE = 48000

class AccDataAnalyser:
    def __init__(self, port, address, smoothing=0):
        self.port = port
        self.address = address
        self.smoothing = smoothing
        
        self._buffer_size = 128
        self._buffer_time = float(BUFFER_SIZE)/SAMP_RATE
        self._buffer_count = -1
        self._buffer = NewTable(self._buffer_time, chnls=3)
        self._data = []
        self._type = None
        
        self._createOSC(port, address)
        self._metro = Metro(self._buffer_time)
        self._table_rec = TrigTableRec([self._oscx,self._oscy,self._oscz], self._metro, self._buffer).stop()
        self._trig_dump = TrigFunc(self._table_rec['trig'], self._dump).stop()
        
    def _createOSC(self, port, address):
        if isinstance(address, list) and len(address) == 3:
            self._type = "simple"
            self._osc = OscReceive(port=port, address=address)
        elif isinstance(address, str):
            self._type = "list"
            self._osc = OscListReceive(port=port, address=address, num=3)
        else:
            print ">>>class AccDataAnalyser :\n<Error type: 'address' attribute must contain either 1 or 3 addresses>"
        self._createScaleObjs()
        
    def _createScaleObjs(self):
        if self._type == "simple":
            self._oscx = Scale(self._osc[self.address[0]], inmin=-1, inmax=1, outmin=-90, outmax=90)
            self._oscy = Scale(self._osc[self.address[1]], inmin=-1, inmax=1, outmin=-90, outmax=90)
            self._oscz = Scale(self._osc[self.address[2]], inmin=-1, inmax=1, outmin=-90, outmax=90)
        elif self._type == "list":
            self._oscx = Scale(self._osc[self.address][0], inmin=-1, inmax=1, outmin=-90, outmax=90)
            self._oscy = Scale(self._osc[self.address][1], inmin=-1, inmax=1, outmin=-90, outmax=90)
            self._oscz = Scale(self._osc[self.address][2], inmin=-1, inmax=1, outmin=-90, outmax=90)

    def _convert_data(self, buffer):
        x_data = []
        y_data = []
        z_data = []
        for i in range(self._buffer_size):
            x, y, z = buffer[0].get(i), buffer[1].get(i), buffer[2].get(i)
            degx = degrees(atan2(-y, -z) + pi);
            degy = degrees(atan2(-x, -z) + pi);
            degz = degrees(atan2(-y, -x) + pi);
            x_data.append(degx)
            y_data.append(degy)
            z_data.append(degz)
        return [x_data, y_data, z_data]
        
    def _dump(self):
        self._pending = self._buffer.copy()
        self._data.append(self._convert_data(self._pending))
        self._buffer_count += 1
        #Que fais-je maintenant de mes précieux échantillons?
        
    def _print_data(self):
        self.cpt += 1
        if self.cpt <= self.num:
            print "Buffer %d :" % self._buffer_count
            print self._data[self._buffer_count]
        else:
            print "---------------------------------------------------------"
            self.trig_print.stop()
            del self.cpt
            del self.num
            del self.trig_print
            if hasattr(self, 'percent'):
                del self.percent
            
            
    ########################
    ## Methodes publiques ##
    ########################
    def play(self):
        self._metro.play()
        self._table_rec.play()
        self._trig_dump.play()
        return self
        
    def stop(self):
        self._metro.stop()
        self._table_rec.stop()
        self._trig_dump.stop()
        
    def print_data(self, num, step=1):
        self.cpt = 0
        self.num = num
        print "\n>>>class AccDataAnalyser"
        if step > 1:
            print "[[X list], [Y list], [Z list]] Data for %d buffers in steps of %d." % (num, step)
            self.percent = Percent(self._table_rec['trig'], percent=100./step)
            self.trig_print = TrigFunc(self.percent, self._print_data)
        else:
            print "[[X list], [Y list], [Z list]] Data for %d buffer(s)." % num
            self.trig_print = TrigFunc(self._table_rec['trig'], self._print_data)
        
        
if __name__ == "__main__":
    from pyo import Server
    s = Server(sr=SAMP_RATE, buffersize=BUFFER_SIZE).boot()
    
    acc = AccDataAnalyser(12000, "/accxyz").play()
    #acc.print_data(4,10)
    s.gui(locals())