#!/usr/bin/env python
# encoding: utf-8

"""
Dernières modifications : mardi 21 mars 2014
Alexandre Poirier
"""

from math import degrees, pi, atan2
from pyo import OscReceive, OscListReceive, OscSend, Scale, Metro, TrigFunc, CallAfter, Trig, SigTo, NewTable, TableRec, TableRead, Sig, Clean_objects, SfPlayer, LinTable
from copy import copy
import numpy
import glob
import wx
from time import time, sleep, strftime

BUFFER_SIZE = 256
SAMP_RATE = 48000

class AccDataReceiver:
    """
    >>>class AccDataReceiver
    
    Receives accelerometre data, converts it to degrees and smoothes it.
    
    Attr : port : Integer. Port to listen on.
           address : String. Address(es) that carries the data.
           smoothing : Boolean. Applies a gaussian smoother.
    
    Notes : - Give only one address if the stream is a list. If the
              data is coming on three different addresses, put them
              in a list as follows ["x_addr", "y_addr", "z_addr"].
            
            - Attributes are available at initialization only.
           
    User can retreive original streams as follows : obj['coord']
    where coord is x, y or z.
    
    User can also retreive a stream of triggers informing when a buffer
    has been filled the following way : obj['trig'].
    """
    def __init__(self, port, address, inmin=-1, inmax=1, smoothing=True):
        self.port = port
        self.address = address
        self._inmin = inmin
        self._inmax = inmax
        
        self._data = []
        self._buffer = []
        self._buffer_size = 64
        self._buffer_count = -1
        self._precision = float(BUFFER_SIZE)/SAMP_RATE
        self._trig_buffer = Trig().stop()
        self._type = None
        
        self._createOSC(port, address)
        self._metro = Metro(self._precision).play()
        if smoothing:
            self._trig_fill = TrigFunc(self._metro, self._fill_buffer_w_smooth)
        else:
            self._trig_fill = TrigFunc(self._metro, self._fill_buffer_wo_smooth)
        
    def __getitem__(self, i):
        if i == 'trig':
            return self._trig_buffer
        if i == 'x':
            return self._oscx
        if i == 'y':
            return self._oscy
        if i == 'z':
            return self._oscz
        
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
            self._oscx = Scale(self._osc[self.address[0]], inmin=self._inmin, inmax=self._inmax, outmin=-90, outmax=90)
            self._oscy = Scale(self._osc[self.address[1]], inmin=self._inmin, inmax=self._inmax, outmin=-90, outmax=90)
            self._oscz = Scale(self._osc[self.address[2]], inmin=self._inmin, inmax=self._inmax, outmin=-90, outmax=90)
        elif self._type == "list":
            self._oscx = Scale(self._osc[self.address][0], inmin=self._inmin, inmax=self._inmax, outmin=-90, outmax=90)
            self._oscy = Scale(self._osc[self.address][1], inmin=self._inmin, inmax=self._inmax, outmin=-90, outmax=90)
            self._oscz = Scale(self._osc[self.address][2], inmin=self._inmin, inmax=self._inmax, outmin=-90, outmax=90)

    def _convert_data(self):
        x, y, z = self._oscx.get(), self._oscy.get(), self._oscz.get()
        degx = degrees(atan2(-y, -z) + pi)
        degy = degrees(atan2(-x, -z) + pi)
        degz = degrees(atan2(-y, -x) + pi)
        return [degx,degy,degz]
        
    ## Method when smoothing is on
    def _dump_w_smooth(self):
        self._pending = copy(self._buffer)
        del self._buffer[:]
        self._buffer_count += 1
        self.call = CallAfter(self._smoother, .005)
        
    ## Method when smoothing is on
    def _fill_buffer_w_smooth(self):
        if len(self._buffer) < self._buffer_size:
            self._buffer.append(self._convert_data())
        else:
            self._dump_w_smooth()
            self._buffer.append(self._convert_data())
            
    ## Method when smoothing is off
    def _dump_wo_smooth(self):
        self._pending = copy(self._buffer)
        del self._buffer[:]
        self._buffer_count += 1
        self.call = CallAfter(self._reorder, .005)
        
    ## Method when smoothing is off
    def _fill_buffer_wo_smooth(self):
        if len(self._buffer) < self._buffer_size:
            self._buffer.append(self._convert_data())
        else:
            self._dump_wo_smooth()
            self._buffer.append(self._convert_data())
        
    def _print_data(self):
        self.cpt += 1
        if self.cpt <= self.num:
            self.temp_data.append(self._pending)
            self.temp_id.append(self._buffer_count)
        else:
            self.trig_print.stop()
            if self.print_mode == 0:
                print "\n>>>class AccDataAnalyser :"
                print "Data for %d buffer(s)." % self.num
                for i in range(self.num):
                    print "\nBuffer %d" % self.temp_id[i]
                    print "------------------------------------"
                    for j in range(self._buffer_size):
                        print "X: %.3f, Y: %.3f, Z: %.3f" % (self.temp_data[i][j][0],
                                                             self.temp_data[i][j][1],
                                                             self.temp_data[i][j][2])
                print "------------------------------------"
            elif self.print_mode == 1:
                file = open(SAVE_PATH+"RAW_DATA_ACCELEROMETER.txt", "w")
                for i in range(self.num):
                    file.write("Buffer %d\n" % self.temp_id[i])
                    for j in range(3):
                        if j == 0:
                            file.write("X : [")
                        if j == 1:
                            file.write("Y : [")
                        if j == 2:
                            file.write("Z : [")
                        for k in range(self._buffer_size):
                            file.write("%.3f" % self.temp_data[i][k][j])
                            if k < self._buffer_size-1:
                                file.write(", ")
                        file.write("]")
                        file.write("\n")
                    if i < self.num-1:
                        file.write("\n")
                file.close()
            del self.trig_print
            del self.cpt
            del self.temp_data
            del self.temp_id
            del self.num
            del self.print_mode
            
    def _reorder(self):
        x = [self._pending[i][0] for i in range(self._buffer_size)]
        y = [self._pending[i][1] for i in range(self._buffer_size)]
        z = [self._pending[i][2] for i in range(self._buffer_size)]
        
        self._data.append([x, y, z])
        self._trig_buffer.play()
        
    def _smoother(self, degree=5):
        x = [self._pending[i][0] for i in range(self._buffer_size)]
        y = [self._pending[i][1] for i in range(self._buffer_size)]
        z = [self._pending[i][2] for i in range(self._buffer_size)]
        
        smooth_x = self._gaussianListSmoother(x)
        smooth_y = self._gaussianListSmoother(y)
        smooth_z = self._gaussianListSmoother(z)
        
        self._data.append([smooth_x, smooth_y, smooth_z])
        self._trig_buffer.play()
        
    def _gaussianListSmoother(self, buffer, degree=5):
        """
        Smoothing algorithm from Scott W. Harden
        Source : http://www.swharden.com/blog/2008-11-17-linear-data-smoothing-in-python/
        """
        #Solution temporaire pour agrandir la liste de 9 elems
        #l'algorithme perd des donnees en cours de route
        #valide seulement pour un buffer de 64 et un degree de 5
        list = [buffer[0]]*5
        for i in range(len(buffer)):list.append(buffer[i])
        for i in range(4):list.append(buffer[-1])
        #########################################
        window=degree*2-1  

        weight=numpy.array([1.0]*window)
        weightGauss=[]
        
        for i in range(window):  
            i=i-degree+1
            frac=i/float(window)
            gauss=1/(numpy.exp((4*(frac))**2))
            weightGauss.append(gauss)
            
        weight=numpy.array(weightGauss)*weight  
        smoothed=[0.0]*(len(list)-window)  

        for i in range(len(smoothed)):
            smoothed[i]=sum(numpy.array(list[i:i+window])*weight)/sum(weight)
        
        return smoothed
            
    ########################
    ## Methodes publiques ##
    ########################
    def get(self):
        """
        Returns last completed buffer after being smoothed.
        """
        return self._data[self._buffer_count]
        
    def getData(self):
        """
        Returns all data since the begining of the app.
        Data is smoothed and not raw.
        """
        return self._data
        
    def getBufferSize(self):
        return self._buffer_size
        
    def play(self):
        """
        Starts processing the accelerometer data.
        """
        self._metro.play()
        self._trig_fill.play()
        self._osc.play()
        return self
        
    def stop(self):
        """
        Stops processing the accelerometer data.
        """
        self._metro.stop()
        self._trig_fill.stop()
        self._osc.stop()
        return self
        
    def print_data(self, num, mode=0):
        """
        num : nunmber of buffers to print
        mode=0 : prints info on screen
        mode=1 : saves data to a .txt file where specified in the preferences
        """
        self.cpt = 0
        self.num = num
        self.temp_data = []
        self.temp_id = []
        self.print_mode = mode
        self.trig_print = TrigFunc(self._trig_buffer, self._print_data)
        
class AccDataAnalyser:
    """
    >>>class AccDataAnalyser
    
    Uses data from AccDataReceiver to create meta-variables.
    
    Attr : obj : AccDataReceiver object.
           threshold : Integer. (0 < x <= 180) Used to calculate roughness.
           rev_x, y & z : Boolean. Reverses the accelerometre data if necessary.
           
    Methods : setThreshold(x) : Set the threshold attribute.
    
    Outputs three audio streams representing the magnitude of the
    movements, roughness of the movements and general activity.
    
    User can retreive these streams by writing, respectively :
    obj['mag'], obj['rgh'] and obj['act'].
    """
    def __init__(self, obj, threshold=10, rev_x=False, rev_y=False, rev_z=False):
        self._obj = obj
        self._threshold = threshold
        self._inversions = {'x':rev_x, 'y':rev_y, 'z':rev_z}
        self._buffer_size = self._obj.getBufferSize()
        
        # Variables d'analyse
        ## mov_ambitus represente le degre de mouvement possible
        ## a l'interieur d'un buffer. Je l'evalue a 30 degre pour l'instant.
        self._mov_ambitus = 30
        self._weights = {'x':.1, 'y':.45, 'z':.45}
        port = float(BUFFER_SIZE)/SAMP_RATE*self._buffer_size
        self._mov_magnitude = SigTo(0, port)
        self._mov_activity = SigTo(0, 1)
        self._mov_roughness = SigTo(0, port)
        
        self._trig_analyse = TrigFunc(self._obj['trig'], self._update)
        
    def __getitem__(self, i):
        if i == 'mag':
            return self._mov_magnitude
        if i == 'rgh':
            return self._mov_roughness
        if i == 'act':
            return self._mov_activity
        
    def _update(self):
        buffer = self._obj.get()
        x = numpy.array(buffer[0])
        y = numpy.array(buffer[1])
        z = numpy.array(buffer[2])
        
        self._mov_magnitude.value = (abs(x[0] - x[-1])/self._mov_ambitus*self._weights['x'] +
                                     abs(y[0] - y[-1])/self._mov_ambitus*self._weights['y'] +
                                     abs(z[0] - z[-1])/self._mov_ambitus*self._weights['z'])
        
        self._mov_activity.value = (numpy.std(x)*self._weights['x'] + 
                                    numpy.std(y)*self._weights['y'] + 
                                    numpy.std(z)*self._weights['z'])
        
        self._mov_roughness.value = (self._calculateRoughness(x)*self._weights['x'] +
                                     self._calculateRoughness(y)*self._weights['y'] +
                                     self._calculateRoughness(z)*self._weights['z'])
        
    def _calculateRoughness(self, coord):
        a = (coord[-1] - coord[0]) / (self._buffer_size-1)
        line = [a*i+coord[0] for i in range(self._buffer_size)]
        rough_count = 0
        
        for i in range(self._buffer_size):
            if abs(coord[i]-line[i]) > self._threshold:
                rough_count += 1
        
        return rough_count
        
    ########################
    ## Methodes publiques ##
    ########################
    def play(self):
        """
        Starts processing acceleromter data.
        """
        self._mov_magnitude.play()
        self._mov_activity.play()
        self._mov_roughness.play()
        self._trig_analyse.play()
        return self
        
    def stop(self):
        """
        Stops processing acceleromter data.
        """
        self._trig_analyse.stop()
        self._mov_magnitude.stop()
        self._mov_activity.stop()
        self._mov_roughness.stop()
        return self
        
    def setThreshold(self, x):
        self._threshold = x
        
    @property
    def threshold(self):
        return self._threshold
    @threshold.setter
    def threshold(self, x):self.setThreshold(x)
    
class AccDataSend:
    """
    >>>class AccDataSend
    
    Gethers all streams from AccDataReceiver & AccDataAnalyser and sends
    them over OSC.
    
    Attr : receiver : AccDataReceiver object.
           analyser : AccDataAnalyser object.
           port : Port to send streams on.
           host : Target host to receive the streams.
           mapping : Addresses used to send the streams over.
           
    Note : The defalut mapping is the following :
                original x-axis (-1 to 1) : /accx
                original y-axis (-1 to 1) : /accy
                original z-axis (-1 to 1) : /accz
                magnitude variable (0 to ~5) : /mag
                roughness variable (0 to ~55) : /rgh
                activity variable (0 to ~50) : /act
                
    All attributes are available at initialization only.
    """
    def __init__(self, receiver, analyser, port, host="127.0.0.1", mapping=None):
        self._receiver = receiver
        self._analyser = analyser
        self._port = port
        self._host = host
        self._dict = {'x':self._receiver['x'],
                      'y':self._receiver['y'],
                      'z':self._receiver['z'],
                      'mag':self._analyser['mag'],
                      'rgh':self._analyser['rgh'],
                      'act':self._analyser['act']}
        
        if mapping != None:
            self._mapping = mapping
        else:
            self._mapping = {'x':"/accx",
                             'y':"/accy",
                             'z':"/accz",
                             'mag':"/mag",
                             'rgh':"/rgh",
                             'act':"/act"}
                             
        self._createOSC()
        
    def _createOSC(self):
        streams = []
        addresses = []
        for key in self._mapping:
            addresses.append(self._mapping[key])
            streams.append(self._dict[key])
        self._osc = OscSend(streams, self._port, addresses, self._host)
        
    ########################
    ## Methodes publiques ##
    ########################
    def play(self):
        """
        Starts sending data over OSC.
        """
        self._osc.play()
        
    def stop(self):
        """
        Stops sending data over OSC.
        """
        self._osc.stop()

class AccDataPlayer:
    """
    >>>class AccDataSend
    
    Gethers all streams from AccDataReceiver & AccDataAnalyser and sends
    them over OSC.
    
    Attr : playlist : A list containing info on the files to play.
                      The format is : [path, repeats, type]
           port : Port to send streams on.
           host : Target host to receive the streams.
           mapping : Addresses used to send the streams over.
           
    Note : The defalut mapping is the following :
                original x-axis (-1 to 1) : /accx
                original y-axis (-1 to 1) : /accy
                original z-axis (-1 to 1) : /accz
                magnitude variable (0 to ~5) : /mag
                roughness variable (0 to ~55) : /rgh
                activity variable (0 to ~50) : /act
                
    All attributes are available at initialization only.
    """
    def __init__(self, playlist, port, host="127.0.0.1", mapping=None, offset=0):
        ##format de la playlist [[path, nbRepeats, type, linkId],[...]]
        self._playlist = playlist
        self._port = port
        self._host = host
        #self.stby_player = SfPlayer("Ressources/blank.wav", loop=True).play()
        
        ##creation des streams pour wrapper les SfPlayer
        self._raw_stream = Sig([0,0,0])
        self._analyzed_stream = Sig([0,0,0])
        
        self._repeats_count = 0
        self.offset = offset
        self._snd_count = offset
        
        self._end_trig = Trig().stop()
        self._snd_trig = Trig().stop()
        self._trig_func = TrigFunc(self._end_trig, self._checkRepeats)
        
        self._setMapping(mapping)
        self._createOSC()
        self._loadNextSnd()
        
    def __getitem__(self, i):
        if i == 'end':
            return self._end_trig
        if i == 'snd':
            return self._snd_trig
    
    def _createOSC(self):
        addresses = [self._mapping['x'], self._mapping['y'], self._mapping['z'],
                     self._mapping['mag'], self._mapping['rgh'], self._mapping['act']]
        self._osc = OscSend([self._raw_stream[0],self._raw_stream[1],self._raw_stream[2],
                            self._analyzed_stream[0],self._analyzed_stream[1],self._analyzed_stream[2]],
                            self._port, addresses, self._host)
                            
    def _setMapping(self, mapping):
        if mapping != None:
            self._mapping = mapping
        else:
            self._mapping = {'x':"/accx",
                             'y':"/accy",
                             'z':"/accz",
                             'mag':"/mag",
                             'rgh':"/rgh",
                             'act':"/act"}
        
    def _loadNextSnd(self):
        if self._snd_count < len(self._playlist):
            
            if (self._snd_count - self.offset) !=0:
                ##annoncer la fin de la lecture d'un element de la liste et de ses repetitions
                self._snd_trig.play()
            
            self._repeats_count = 0
            
            ##looping est-il necessaire?
            loop = True if self._playlist[self._snd_count][1] > 1 else False
            
            ##verifie si le fichier a lire est lie a un autre
            if self._playlist[self._snd_count][3] != -1:
                if self._playlist[self._snd_count][2] == 0:
                    analyzedPlayer = SfPlayer(self._playlist[self._snd_count][0], loop=loop, mul=[6,64,100]).play()
                    rawPlayer = SfPlayer(self._playlist[self._snd_count+1][0], loop=loop, mul=90).play()
                else:
                    analyzedPlayer = SfPlayer(self._playlist[self._snd_count+1][0], loop=loop, mul=[6,64,100]).play()
                    rawPlayer = SfPlayer(self._playlist[self._snd_count][0], loop=loop, mul=90).play()
                self._analyzed_stream.setValue(analyzedPlayer)
                self._raw_stream.setValue(rawPlayer)
                
                ##changer le input pour capter la fin de la lecture du fichier son
                self._trig_func.setInput(analyzedPlayer['trig'])
            else:
                ##determine si le fichier est analyse ou brute
                if self._playlist[self._snd_count][2] == 0:
                    sndPlayer = SfPlayer(self._playlist[self._snd_count][0], loop=loop, mul=[6,64,100]).play()
                    
                    self._analyzed_stream.setValue(sndPlayer)
                    self._raw_stream.setValue([0,0,0])
                else:
                    sndPlayer = SfPlayer(self._playlist[self._snd_count][0], loop=loop, mul=90).play()
                    
                    self._raw_stream.setValue(sndPlayer)
                    self._analyzed_stream.setValue([0,0,0])
                
                ##changer le input pour capter la fin de la lecture du fichier son
                self._trig_func.setInput(sndPlayer['trig'])
        else:
            self.stop()
            self._end_trig.play()
                
    def _checkRepeats(self):
        self._repeats_count += 1
        
        if self._repeats_count == self._playlist[self._snd_count][1]:
            if self._playlist[self._snd_count][3] != -1:
                self._snd_count += 2
            else:
                self._snd_count += 1
            self._loadNextSnd()
        
    ########################
    ## Methodes publiques ##
    ########################
    def play(self, offset=0):
        """
        Starts sending data over OSC.
        """
        self._snd_count = offset
        self._osc.play()
        self._raw_stream.play()
        self._analyzed_stream.play()
        self._trig_func.play()
        self._loadNextSnd()
        
    def stop(self):
        """
        Stops sending data over OSC.
        """
        self._osc.stop()
        self._raw_stream.setValue([0,0,0])
        self._analyzed_stream.setValue([0,0,0])
        self._trig_func.stop()
        
    def setPlaylist(self, newList):
        self._playlist = newList
        
    def setOSC(self, port, host, mapping=None):
        self._port = port
        self._host = host
        self._setMapping(mapping)
        self._createOSC()
        
    def getCount(self):
        return self._snd_count+1

class RecordModule:
    def __init__(self, parent, receiver, analyzer, rec_time=60, raw_data=False, file_ext=0):
        self._parent = parent
        self._receiver = receiver
        self._analyzer = analyzer
        self._raw_data = raw_data
        self._filename_type = file_ext #0= chiffres ou 1=date et heure
        self._rec_time = rec_time
        self._num_rec = -1
        self.start_time = 0
        #Sauvegarde le temps reel d'enregistrement en secondes
        self._actual_rec_time = []
        self._save_analyzed = []
        self._save_raw = []
        
        if self._raw_data:
            self.raw_list = [NewTable(length=self._rec_time, chnls=3)]
            self.analyzed_list = [NewTable(length=self._rec_time, chnls=3)]
            
            input_raw = Sig([self._receiver['x']/90,
                             self._receiver['y']/90,
                             self._receiver['z']/90])
            input_analyzed = Sig([self._analyzer['mag']/6,
                                  self._analyzer['rgh']/64,
                                  self._analyzer['act']/100])
                      
            self._tablerec_raw = TableRec(input=input_raw, table=self.raw_list[0])
            self._tablerec_analyzed = TableRec(input=input_analyzed, table=self.analyzed_list[0])
        else:
            self.analyzed_list = [NewTable(length=self._rec_time, chnls=3)]
            
            input_analyzed = Sig([self._analyzer['mag'],self._analyzer['rgh'],self._analyzer['act']])
            
            self._tablerec_analyzed = TableRec(input=input_analyzed, table=self.analyzed_list[0])
            
    def __getitem__(self, i):
        if i == 'trig':
            return self._tablerec_analyzed['trig']
            
    def _createTablesForSave(self):
        nbRecs = self._num_rec+1
        self.dlg = wx.ProgressDialog("Saving...", "Creating files", maximum = nbRecs, parent=self._parent, 
                style = wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME)
        self.count = 0
        #le timer garde la fenetre de progres a jour selon le compte
        timer = Metro(.75).play()
        trigfunc = TrigFunc(timer, self._updateProgress)
        if self._raw_data:
            for i in range(nbRecs):
                #creation de nouvelles tables avec la duree reelle des enreg.
                self._save_analyzed.append(NewTable(length=self._actual_rec_time[i], chnls=3))
                self._save_raw.append(NewTable(length=self._actual_rec_time[i], chnls=3))
                #population des nouvelles tables echantillon par echantillon
                for samp in range(self._save_analyzed[i].getSize(False)):
                    self._save_analyzed[i][0].put(self.analyzed_list[i][0].get(samp), samp)
                    self._save_analyzed[i][1].put(self.analyzed_list[i][1].get(samp), samp)
                    self._save_analyzed[i][2].put(self.analyzed_list[i][2].get(samp), samp)
                    self._save_raw[i][0].put(self.raw_list[i][0].get(samp), samp)
                    self._save_raw[i][1].put(self.raw_list[i][1].get(samp), samp)
                    self._save_raw[i][2].put(self.raw_list[i][2].get(samp), samp)
                self.count += 1
        else:
            for i in range(nbRecs):
                self._save_analyzed.append(NewTable(length=self._actual_rec_time[i], chnls=3))
                for samp in range(self._save_analyzed[i].getSize(False)):
                    self._save_analyzed[i][0].put(self.analyzed_list[i][0].get(samp), samp)
                    self._save_analyzed[i][1].put(self.analyzed_list[i][1].get(samp), samp)
                    self._save_analyzed[i][2].put(self.analyzed_list[i][2].get(samp), samp)
                self.count += 1
        timer.stop()
        trigfunc.stop()
        del timer
        del trigfunc
        del self.count
            
    def _updateProgress(self):
        self.dlg.Update(self.count)
        wx.Yield()
    
    def clean(self):
        self._reset()
        self.cleaner = Clean_objects(.1, self.analyzed_list)
        
    def _getFileNum(self, path):
        if wx.Platform == '__WXMSW__':
            slash = path.rfind("\\")
        else:
            slash = path.rfind("/")
        folder = path[:slash+1]
        file = path[slash+1:]
        list = glob.glob(folder+"*")
        
        if list == []:
            return 1
        else:
            num = 0
            index = []
            for i, f in enumerate(list):
                if f.rfind(file) != -1:
                    index.append(i)
            for i in index:
                dot = list[i].rfind(".")
                try:
                    #verifie le caractere avant le point
                    temp_num = int(list[i][dot-1])
                except ValueError:
                    pass
                else:
                    try:
                        #verifie si nombre a deux chiffres
                        temp = int(list[i][dot-2])
                    except ValueError:
                        pass
                    else:
                        temp_num = int(list[i][dot-2:dot])
                    num = temp_num if temp_num > num else num
            return num+1
        
    def getNumTracks(self):
        return self._num_rec+1
    
    def record(self):
        self._num_rec += 1
        
        if self._raw_data:
            if self._num_rec > 0:
                self.raw_list.append(NewTable(length=self._rec_time, chnls=3))
                self.analyzed_list.append(NewTable(length=self._rec_time, chnls=3))
                
                self._tablerec_raw.setTable(self.raw_list[self._num_rec])
                self._tablerec_analyzed.setTable(self.analyzed_list[self._num_rec])
                
            self.start_time = time()
            self._tablerec_analyzed.play()
            self._tablerec_raw.play()
        else:
            if self._num_rec > 0:
                self.analyzed_list.append(NewTable(length=self._rec_time, chnls=3))
                self._tablerec_analyzed.setTable(self.analyzed_list[self._num_rec])
            self.start_time = time()
            self._tablerec_analyzed.play()
        
    def _reset(self):
        #supprime les tables d'enreg. et re-init les listes
        if self._raw_data:
            self.raw_list = [NewTable(length=self._rec_time, chnls=3)]
            self._tablerec_raw.setTable(self.raw_list[0])
            self._save_raw = []
        self.analyzed_list = [NewTable(length=self._rec_time, chnls=3)]
        self._tablerec_analyzed.setTable(self.analyzed_list[0])
        self._actual_rec_time = []
        self._save_analyzed = []
        self._num_rec = -1
    
    def stopRec(self):
        self._tablerec_analyzed.stop()
        if self._raw_data:
            self._tablerec_raw.stop()
        secs = time() - self.start_time
        self._actual_rec_time.append(secs)
        
    def saveToDisk(self, path):
        start = time()
        self._createTablesForSave()
        self.dlg.UpdatePulse("Writing to disk...")
        wx.Yield()
        try:
            index = path.rindex(".")
            ext = path[index:]
            path = path[:index]
        except ValueError:
            ext = ".wav"
        
        if self._raw_data:
            if self._filename_type:
                date = strftime("_%d_%b_%Y_%Hh%M")
                for i in range(self._num_rec+1):
                    path_raw = path + "_raw" + date + ext
                    path_an = path + "_analyzed" + date + ext
                    self._save_raw[i].save(path_raw, sampletype=1)
                    self._save_analyzed[i].save(path_an, sampletype=1)
            else:
                num = self._getFileNum(path)
                for i in range(self._num_rec+1):
                    path_raw = path + "_raw" + str(i+num) + ext
                    path_an = path + "_analyzed" + str(i+num) + ext
                    self._save_raw[i].save(path_raw, sampletype=1)
                    self._save_analyzed[i].save(path_an, sampletype=1)
        else:
            if self._filename_type:
                date = strftime("_%d_%b_%Y_%Hh%M")
                for i in range(self._num_rec+1):
                    new_path = path + date + ext
                    self._save_analyzed[i].save(new_path, sampletype=1)
            else:
                num = self._getFileNum(path)
                for i in range(self._num_rec+1):
                    new_path = path + str(i+num) + ext
                    self._save_analyzed[i].save(new_path, sampletype=1)
        #on re-init les tables pour sauver de la memoire
        self._reset()
        self.dlg.Destroy()
        print "Finished saving after : %.2f sec." % (time()-start)

if __name__ == "__main__":
    from pyo import Server, Print
    s = Server(buffersize=BUFFER_SIZE).boot().start()
    
    receiver = AccDataReceiver(9000, "/accxyz", False)
    #receiver.print_data(4)
    analyser = AccDataAnalyser(receiver)
    printstreams = Print([analyser['mag'],analyser['rgh'],analyser['act']], message=["Magnitude","Roughness","Activity"])
    
    s.gui(locals())
