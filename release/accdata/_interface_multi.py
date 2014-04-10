#!/usr/bin/env python
# encoding: utf-8

"""
ACC Data Player interface - _interface_multi.py
Alexandre Poirier
Dernière moifications : mardi 8 avril 2014

Améliorations à apporter
    - Terminer la fenêtre Help.
    - Tester et adapter mon programme aux multiples plateformes. 
      (Linux & Windows)
"""

import wx
import os
import sys
#import threading
from _player_interface import *
from Ressources._utilitaires import getLocalIP
from time import sleep, strftime, time
from Ressources._help import HELP_TEXT

HOME_PATH = os.path.expanduser("~")
SAVE_PATH = os.path.join(HOME_PATH, "Documents", "AccData")
LOCAL_IP = getLocalIP()

##Import icones perso (PyEmbeddedImage)
if wx.Platform == '__WXMAC__':
    from Ressources.config.mac import config
    from Ressources.img.mac_icons import catalog
elif wx.Platform == '__WXGTK__':
    from Ressources.config.gtk import config
    from Ressources.img.default_icons import catalog
elif wx.Platform == '__WXMSW__':
    from Ressources.config.msw import config
    from Ressources.img.default_icons import catalog

#A supprimer eventuellement
##Constantes pour icones perso
#ID_BTN_START = "01"
#ID_BTN_PAUSE = "02"
#ID_BTN_REC = "03"
#ID_BTN_SETTINGS = "04"
#ID_BTN_LOG = "05"
#ID_BTN_MONITOR = "06"
#ID_BTN_SAVE = "07"
#ID_BTN_PLAYER = "09"
#ID_SEP = "08"
ITEM_START, ITEM_PAUSE, ITEM_REC, ITEM_SAVE, ITEM_PLAYER = 4,5,6,8,9
ITEMS_SEP = [3,7]

##Dictionnaire de variables qui enregistre l'etat du programme
PRGM_STATE = {'IS_PLAYING':False,
              'IS_RECORDING':False,
              'IS_READY':False,
              'IS_RUNNING':True}

##Dictionnaire de variables de temps [temps total, debut cycle, fin cycle]
PRGM_TIME = {'playing':[0.,0.,0.],'recording':[0.,0.,0.]}

def calcRunTime(start, current):
    """
    Takes start time and current time in seconds
    (as provided by time.time()) and calculates
    the running time.
    
    Return a tuple as follows : (hour, min, sec)
    """
    run_time = current - start
    hour = min = sec = 0
    
    if run_time > 60:
        min = int(run_time / 60)
        if min > 60:
            hour = int(min / 60)
            min = int(min%60)
    sec = int(run_time%60)
    
    return (hour,min,sec)

#A supprimer eventuellement            
#class AccArtProvider(wx.ArtProvider):
#    def __init__(self):
#        wx.ArtProvider.__init__(self)

#    def CreateBitmap(self, artid, client, size):
#        bmp = wx.NullBitmap
#        if artid == ID_BTN_START:
#            bmp = wx.Bitmap(ART_BTN_START, wx.BITMAP_TYPE_PNG)
#        elif artid == ID_BTN_PAUSE:
#            bmp = wx.Bitmap(ART_BTN_PAUSE, wx.BITMAP_TYPE_PNG)
#        elif artid == ID_BTN_REC:
#            bmp = wx.Bitmap(ART_BTN_REC, wx.BITMAP_TYPE_PNG)
#        elif artid == ID_BTN_SETTINGS:
#            bmp = wx.Bitmap(ART_BTN_SETTINGS, wx.BITMAP_TYPE_PNG)
#        elif artid == ID_BTN_LOG:
#            bmp = wx.Bitmap(ART_BTN_LOG, wx.BITMAP_TYPE_PNG)
#        elif artid == ID_BTN_MONITOR:
#            bmp = wx.Bitmap(ART_BTN_MONITOR, wx.BITMAP_TYPE_PNG)
#        elif artid == ID_BTN_SAVE:
#            bmp = wx.Bitmap(ART_BTN_SAVE, wx.BITMAP_TYPE_PNG)
#        elif artid == ID_SEP:
#            bmp = wx.Bitmap(ART_SEP, wx.BITMAP_TYPE_PNG)
#        elif artid == ID_BTN_PLAYER:
#            bmp = wx.Bitmap(ART_BTN_PLAYER, wx.BITMAP_TYPE_PNG)
#        bmp.SetSize(size)
#        return bmp

class MainFrame(wx.Frame):
    def __init__(self, parent, title, pos, size, style):
        wx.Frame.__init__(self, parent=parent, title=title, pos=pos, size=size, style=style)
        ##Garde une reference au thread pour le terminer avant de quitter
        self.thread = None
        ##Garde une reference au module d'enregistrement pour communiquer
        self.rec_module = None
        ##Garde une reference du serveur audio
        self.audio_server = None
        ##Garde une reference a la fonction _apply du settings_panel
        self.fctSave = None
        ##Conserve les options d'enregistrement en memoire
        self._rec_options = {'rec_time':60,'raw_data':0,'path':SAVE_PATH,'name':"accdata",'file_ext':0}
        wx.CallLater(500, self._importUserRecOptions)
        ##Creation du dossier de sauvegarde, si necessaire
        self._createFolder(SAVE_PATH)
        
        menubar = wx.MenuBar()
        filemenu = wx.Menu()
        
        saveitem = filemenu.Append(100, "Save Preferences\tCtrl+S","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._save, id=100)
        
        saverecitem = filemenu.Append(101, "Save Data\tCtrl+alt+S","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._saveRec, id=101)
        
        quititem = filemenu.Append(102,"Quit\tCtrl+Q","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU,self._onQuit, id=102)
        self.Bind(wx.EVT_CLOSE,self._onQuit)
        menubar.Append(filemenu, "&Menu")
        
        actionmenu = wx.Menu()
        startitem = actionmenu.Append(202, "Start processing\tCtrl+Shift+S","",wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self._start, id=202)
        
        recitem = actionmenu.Append(200, "Record\tCtrl+R","", wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self._record, id=200)
        
        recprefsitem = actionmenu.Append(201, "Record options\tCtrl+Shift+R","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._recordOptions, id=201)
        menubar.Append(actionmenu, "&Action")
        
        helpmenu = wx.Menu()
        aboutitem = helpmenu.Append(300, "About","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU,self._about, id=300)
        helpitem = helpmenu.Append(301, "Help","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU,self._help, id=301)
        menubar.Append(helpmenu, "&Help")
        
        self.SetMenuBar(menubar)
        
        self.aboutinfo = wx.AboutDialogInfo()
        self.aboutinfo.SetCopyright(u"\xa92014 Alexandre Poirier")
        self.aboutinfo.SetDescription("Transforms regular accelerometer data into\nmeta-variables that can be used with audio\nsoftware to control certain parametres\nduring performance.")
        self.aboutinfo.SetDevelopers(["Alexandre Poirier"])
        self.aboutinfo.SetName("ACC Data Analyzer")
        self.aboutinfo.SetVersion("0.1.0")
        
    ##############################
    ## Methodes propre aux tabs ##
    ##############################
    def CreateTabs(self, tabs):
        """
        Create the toolbar and add a tool for each tab.
        
        tabs -- List of (label, bitmap) pairs.
        """
        
        # Create the toolbar
        self.tabIndex = 0
        self.toolbar = self.CreateToolBar(style=wx.TB_HORIZONTAL|wx.TB_TEXT)
        for i, tab in enumerate(tabs):
            if tab[0] == "Sep":
                self.toolbar.AddCheckTool(id=i, bitmap=tab[1])
            else:
                self.toolbar.AddCheckLabelTool(id=i, label=tab[0], bitmap=tab[1])
        self.toolbar.Realize()
        # Determine whether to invoke the special toolbar handling
        macNative = False
        if wx.Platform == '__WXMAC__':
            if hasattr(self, 'MacGetTopLevelWindowRef'):
                try:
                    import ctypes
                    macNative = True
                except ImportError:
                    pass
        if macNative:
            self.PrepareMacNativeToolBar()
            self.Bind(wx.EVT_TOOL, self.OnToolBarMacNative)
        else:
            self.PrepareRegularToolbar()
            self.Bind(wx.EVT_TOOL, self.OnToolBarDefault)
            
        self.Show()
    
    def OnTabChange(self, tabIndex):
        """Respond to the user switching tabs."""
        pass
        
    def PrepareRegularToolbar(self):
        self.toolbar.ToggleTool(0, True)
        self.toolbar.EnableTool(ITEMS_SEP[0], False)
        self.toolbar.EnableTool(ITEMS_SEP[1], False)
        self.toolbar.EnableTool(ITEM_PAUSE, False)

    def PrepareMacNativeToolBar(self):
        """Extra toolbar setup for OS X native toolbar management."""
            
        # Load the frameworks
        import ctypes
        carbonLoc = '/System/Library/Carbon.framework/Carbon'
        coreLoc = '/System/Library/CoreFoundation.framework/CoreFoundation'
        self.carbon = ctypes.CDLL(carbonLoc)  # Also used in OnToolBarMacNative
        core = ctypes.CDLL(coreLoc)
        # Get a reference to the main window
        frame = self.MacGetTopLevelWindowRef()
        # Allocate a pointer to pass around
        p = ctypes.c_voidp()
        # Get a reference to the toolbar
        self.carbon.GetWindowToolbar(frame, ctypes.byref(p))
        toolbar = p.value
        # Get a reference to the array of toolbar items
        self.carbon.HIToolbarCopyItems(toolbar, ctypes.byref(p))
        #Make icons BIGGER!
        self.carbon.HIToolbarSetDisplaySize(toolbar, 1)
        # Get references to the toolbar items (note: separators count)
        self.macToolbarItems = [core.CFArrayGetValueAtIndex(p, i)
                                for i in xrange(self.toolbar.GetToolsCount())]
        # Set the native "selected" state on the first tab
        # 128 corresponds to kHIToolbarItemSelected (1 << 7)
        item = self.macToolbarItems[self.tabIndex]
        self.carbon.HIToolbarItemChangeAttributes(item, 128, 0)
        # Set the pause button as disabled
        item = self.macToolbarItems[ITEM_PAUSE]
        self.carbon.HIToolbarItemChangeAttributes(item, 64, 0)
        # Set the separators as disabled
        item = self.macToolbarItems[ITEMS_SEP[0]]
        self.carbon.HIToolbarItemChangeAttributes(item, 64, 0)
        item = self.macToolbarItems[ITEMS_SEP[1]]
        self.carbon.HIToolbarItemChangeAttributes(item, 64, 0)

    def OnToolBarDefault(self, event):
        """Ensure that there is always one tab selected."""

        global PRGM_STATE
        i = event.GetId()
        if i in xrange(self.toolbar.GetToolsCount()):
            if i != self.tabIndex:
                if i == ITEM_START:
                    if PRGM_STATE['IS_READY']:
                        PRGM_STATE['IS_PLAYING'] = True
                        self.GetMenuBar().Check(id=202, check=True)
                        self.toolbar.EnableTool(ITEM_START, False)
                        self.toolbar.EnableTool(ITEM_PAUSE, True)
                        self.toolbar.ToggleTool(ITEM_START, False)
                elif i == ITEM_PAUSE:
                    PRGM_STATE['IS_PLAYING'] = False
                    PRGM_STATE['IS_RECORDING'] = False
                    self.rec_module.stopRec()
                    self.GetMenuBar().Check(id=200, check=False)
                    self.GetMenuBar().Check(id=202, check=False)
                    self.toolbar.EnableTool(ITEM_START, True)
                    self.toolbar.EnableTool(ITEM_PAUSE, False)
                    self.toolbar.ToggleTool(ITEM_REC, False)
                    self.toolbar.ToggleTool(ITEM_PAUSE, False)
                elif i == ITEM_REC:
                    if PRGM_STATE['IS_READY']:
                        if PRGM_STATE['IS_RECORDING']:
                            PRGM_STATE['IS_RECORDING'] = False
                            self.rec_module.stopRec()
                            self.GetMenuBar().Check(id=200, check=False)
                            self.toolbar.ToggleTool(ITEM_REC, False)
                        else:
                            if PRGM_STATE['IS_PLAYING']:
                                PRGM_STATE['IS_RECORDING'] = True
                                self.rec_module.record()
                                self.GetMenuBar().Check(id=200, check=True)
                                self.toolbar.ToggleTool(ITEM_REC, True)
                            else:
                                PRGM_STATE['IS_PLAYING'] = True
                                PRGM_STATE['IS_RECORDING'] = True
                                self.rec_module.record()
                                self.GetMenuBar().Check(id=200, check=True)
                                self.GetMenuBar().Check(id=202, check=True)
                                self.OnTabChange(ITEM_START)
                                self.toolbar.ToggleTool(ITEM_REC, True)
                                self.toolbar.EnableTool(ITEM_START, False)
                                self.toolbar.EnableTool(ITEM_PAUSE, True)
                elif i == ITEM_SAVE:
                    event = wx.CommandEvent(winid=ITEM_SAVE)
                    self._saveRec(event)
                    self.toolbar.ToggleTool(ITEM_SAVE, False)
                elif i == ITEM_PLAYER:
                    event = wx.CommandEvent(winid=ITEM_PLAYER)
                    self._openPlayer(event)
                    self.toolbar.ToggleTool(ITEM_PLAYER, False)
                else:
                    self.toolbar.ToggleTool(self.tabIndex, False)
                    self.toolbar.ToggleTool(i, True)
                    self.tabIndex = i
                self.OnTabChange(i)
            else:
                self.toolbar.ToggleTool(self.tabIndex, True)
        else:
            event.Skip()
    
    def OnToolBarMacNative(self, event):
        """Manage the toggled state of the tabs manually."""
        
        global PRGM_STATE
        i = event.GetId()
        if i in xrange(self.toolbar.GetToolsCount()):
            self.toolbar.ToggleTool(i, False)  # Suppress default selection
            if i != self.tabIndex:
                # Set the native selection look via the Carbon APIs
                # 128 corresponds to kHIToolbarItemSelected (1 << 7)
                if i == ITEM_START:
                    if PRGM_STATE['IS_READY']:
                        PRGM_STATE['IS_PLAYING'] = True
                        self.GetMenuBar().Check(id=202, check=True)
                        play = self.macToolbarItems[ITEM_START]
                        self.carbon.HIToolbarItemChangeAttributes(play, 64, 0)
                        pause = self.macToolbarItems[ITEM_PAUSE]
                        self.carbon.HIToolbarItemChangeAttributes(pause, 0, 64)
                elif i == ITEM_PAUSE:
                    PRGM_STATE['IS_PLAYING'] = False
                    PRGM_STATE['IS_RECORDING'] = False
                    self.rec_module.stopRec()
                    self.GetMenuBar().Check(id=200, check=False)
                    self.GetMenuBar().Check(id=202, check=False)
                    play = self.macToolbarItems[ITEM_START]
                    self.carbon.HIToolbarItemChangeAttributes(play, 0, 64)
                    pause = self.macToolbarItems[ITEM_PAUSE]
                    self.carbon.HIToolbarItemChangeAttributes(pause, 64, 0)
                elif i == ITEM_REC:
                    if PRGM_STATE['IS_READY']:
                        if PRGM_STATE['IS_RECORDING']:
                            PRGM_STATE['IS_RECORDING'] = False
                            self.rec_module.stopRec()
                            self.GetMenuBar().Check(id=200, check=False)
                        else:
                            if PRGM_STATE['IS_PLAYING']:
                                PRGM_STATE['IS_RECORDING'] = True
                                self.rec_module.record()
                                self.GetMenuBar().Check(id=200, check=True)
                            else:
                                PRGM_STATE['IS_PLAYING'] = True
                                PRGM_STATE['IS_RECORDING'] = True
                                self.rec_module.record()
                                self.GetMenuBar().Check(id=200, check=True)
                                self.GetMenuBar().Check(id=202, check=True)
                                self.OnTabChange(ITEM_START)
                                play = self.macToolbarItems[ITEM_START]
                                self.carbon.HIToolbarItemChangeAttributes(play, 64, 0)
                                pause = self.macToolbarItems[ITEM_PAUSE]
                                self.carbon.HIToolbarItemChangeAttributes(pause, 0, 64)
                elif i == ITEM_SAVE:
                    event = wx.CommandEvent(winid=ITEM_SAVE)
                    self._saveRec(event)
                elif i == ITEM_PLAYER:
                    event = wx.CommandEvent(winid=ITEM_PLAYER)
                    self._openPlayer(event)
                else:
                    item = self.macToolbarItems[i]
                    self.carbon.HIToolbarItemChangeAttributes(item, 128, 0)
                    self.tabIndex = i
                self.OnTabChange(i)
        else:
            event.Skip()
            
    #####################################
    ##            Methodes             ##
    ## Classees par ordre alphabetique ##
    #####################################
    def _animateChangeSize(self, start, end):
        """Animates the change of size"""
        diff_x = start[0]-end[0]
        diff_y = start[1]-end[1]
        abs_diff_x = abs(diff_x)
        abs_diff_y = abs(diff_y)
        bigger = abs_diff_x if abs_diff_x > abs_diff_y else abs_diff_y
        
        if bigger < 70:
            step = 5
        else:
            step = 6
        
        factor = 3
        pixel_step = float(bigger)/step
        time_list = [2**((i+1.)/pixel_step)/(pixel_step*factor) for i in range(step)]
        
        x_step = abs_diff_x/step
        y_step = abs_diff_y/step
        
        if diff_x < 0 and diff_y < 0:
            for i in range(step):
                x, y = self.GetSize()
                wx.Yield()
                
                if i == step-1:
                    x = end[0]
                    y = end[1]
                else:
                    x += x_step
                    y += y_step
                    
                self.SetSize((x,y))
                wx.Yield()
                sleep(time_list[i])
        elif diff_x < 0 and diff_y >= 0:
            for i in range(step):
                x, y = self.GetSize()
                wx.Yield()
                
                if i == step-1:
                    x = end[0]
                    y = end[1]
                else:
                    x += x_step
                    y -= y_step
                
                self.SetSize((x,y))
                wx.Yield()
                sleep(time_list[i])     
        elif diff_x >= 0 and diff_y < 0:
            for i in range(step):
                x, y = self.GetSize()
                wx.Yield()
                
                if i == step-1:
                    x = end[0]
                    y = end[1]
                else:
                    x -= x_step
                    y += y_step
                
                self.SetSize((x,y))
                wx.Yield()
                sleep(time_list[i])
        elif diff_x >= 0 and diff_y >= 0:
            for i in range(step):
                x, y = self.GetSize()
                wx.Yield()
                
                if i == step-1:
                    x = end[0]
                    y = end[1]
                else:
                    x -= x_step
                    y -= y_step
                
                self.SetSize((x,y))
                wx.Yield()
                sleep(time_list[i])

    def _about(self, evt):
        aboutbox = wx.AboutBox(self.aboutinfo)
        
    def changeSize(self, size, smooth=True):
        """
        Changes the size of the window.
        Attr : size : new size to apply as (width, height).
               smooth : calls for an animation or not.
        """
        if size != self.GetSize():
            if smooth:
                self._animateChangeSize(self.GetSize(), size)
            else:
                self.SetSize(size)
                wx.Yield()
    
    def _createFolder(self, path):
        if not os.path.exists(path): 
            os.makedirs(path)
    
    def getRecOptions(self):
        return self._rec_options
    
    def _help(self, evt):
        helpWindow = HelpDialog(self)
        helpWindow.CenterOnParent(wx.BOTH)
        helpWindow.Show()

    def _importUserRecOptions(self):
        try:
            f = open(os.path.join(SAVE_PATH, "record_options.pref"), 'r')
            for line in f:
                key, value = line.split(':',1)
                value = value.replace('\n', '')
                if key in ['rec_time','raw_data','file_ext']:
                    value = int(value)
                self._rec_options[key] = value
        except IOError, e:
            print "No record options saved yet..."
            #print "IOError : %s" % str(e)
        else:
            print "Your record options have been loaded."
            f.close()
    
    def _onQuit(self, evt):
        if hasattr(self, 'player_frame'):
            try:
                self.player_frame.IsShown()
            except:
                pass
            else:
                dialog = wx.MessageDialog(self, 'The ACC Data Player window will close with the application.\nAll unsaved data will be lost.',
                                       'Warning!',
                                       wx.OK | wx.ICON_INFORMATION | wx.CANCEL)
                                       
                if dialog.ShowModal() == wx.ID_OK:
                    self.player_frame.Destroy()
                else:
                    return 0
        
        global PRGM_STATE
        ##Permet de stopper le thread
        PRGM_STATE['IS_RUNNING'] = False
        self.thread.join()
        self.audio_server.stop()
        self.Destroy()
        
    def _openPlayer(self, evt):
        self.player_frame = PlayerFrame(None, size=(1000,600), pos=(100,100))
        self.player_frame.Show()
        
    def _record(self, evt):
        event = wx.CommandEvent(winid=ITEM_REC)
        if wx.Platform == '__WXMAC__':
            self.OnToolBarMacNative(event)
        else:
            self.OnToolBarDefault(event)
            
    def _recordOptions(self, evt):
        dialog = RecordOptions(self, size=(100,100))
        dialog.CenterOnScreen()
        
        dialog.choiceRawData.SetSelection(self._rec_options['raw_data'])
        dialog.time.SetValue(str(self._rec_options['rec_time']))
        dialog.path.SetValue(self._rec_options['path'])
        dialog.name.SetValue(self._rec_options['name'])
        dialog.choiceFileName.SetSelection(self._rec_options['file_ext'])
        
        if dialog.ShowModal() == wx.ID_OK:
            self._rec_options['raw_data'] = dialog.choiceRawData.GetCurrentSelection()
            self._rec_options['rec_time'] = int(dialog.time.GetValue())
            self._rec_options['path'] = self._verifyPath(dialog.path.GetValue())
            self._rec_options['name'] = self._verifyName(dialog.name.GetValue())
            self._rec_options['file_ext'] = dialog.choiceFileName.GetCurrentSelection()
            self._saveRecOptions()
        
        dialog.Destroy()
        
    def _save(self, evt):
        """Saves user settings to disk"""
        event = wx.CommandEvent(winid=0)
        self.fctSave(event)
        
    def _saveRec(self, evt):
        """Saves recordings to disk"""
        self._createFolder(self._rec_options['path'])
        if self.rec_module != None and self.rec_module.getNumTracks() != 0:
            if not PRGM_STATE['IS_PLAYING']:
                print "\nSaving data to disk..."
                path = os.path.join(self._rec_options['path'], self._rec_options['name'])
                self.rec_module.saveToDisk(path)
                print "Done."
                PRGM_TIME['recording'][0] = 0.
            else:
                event = wx.CommandEvent(winid=1)
                if wx.Platform == '__WXMAC__':
                    self.OnToolBarMacNative(event)
                else:
                    self.OnToolBarDefault(event)
                print "< WARNING >\nThe program needs to be stopped before saving data to disk."
        else:
            print "< WARNING >\nNothing to save yet."
    
    def _saveRecOptions(self):
        f = open(os.path.join(SAVE_PATH, "record_options.pref"), 'w')
        for key in self._rec_options:
            f.write(key+':'+str(self._rec_options[key])+'\n')
        f.close()
        print 'Saved record options to disk.'
        
    def _start(self, evt):
        #if evt.GetEventObject().IsChecked(evt.GetId()):
        if self.GetMenuBar().IsChecked(evt.GetId()):
            event = wx.CommandEvent(winid=ITEM_START)
            if wx.Platform == '__WXMAC__':
                self.OnToolBarMacNative(event)
            else:
                self.OnToolBarDefault(event)
        else:
            event = wx.CommandEvent(winid=ITEM_PAUSE)
            if wx.Platform == '__WXMAC__':
                self.OnToolBarMacNative(event)
            else:
                self.OnToolBarDefault(event)
    
    def _verifyName(self, name):
        if name.startswith("/") or name.startswith("\\"):
            name = name[1:]
        return str(name)
    
    def _verifyPath(self, path):
        if path.endswith("/") or path.endswith("\\"):
            path = path[:-1]
        return str(path)
    
class SettingsPanel(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos=pos, size=size, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        self.SetBackgroundColour("#222222")
        
        ##Positions des blocks
        self.osc_block = config['settingsPos']['osc_block']
        self.addresses_block = config['settingsPos']['add_block']
        self.mapping_block = config['settingsPos']['map_block']
        self.analyse_block = config['settingsPos']['ana_block']
        self._user_settings = {}
        self._default_settings = {'portin':"8000",'portout':"10000",'ipout':"127.0.0.1",
                                  'stream_type':0,'addr1':"/accxyz",'addr2':"",'addr3':"",
                                  'map_mag':"/mag",'map_rgh':"/rgh",'map_act':"/act",
                                  'smoothing':True,'thresh':20, 'min':"-1", 'max':"1"}
        
        ##OSC block
        self.pos_portin = (self.osc_block[0], self.osc_block[1]+config['settingsPos']['portin'])
        self.portin = wx.TextCtrl(self, value="", pos=(self.pos_portin[0]+config['settingsPos']['ctrlX'], self.pos_portin[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER)
        self.pos_portout = (self.osc_block[0], self.osc_block[1]+config['settingsPos']['portout'])
        self.portout = wx.TextCtrl(self, value="", pos=(self.pos_portout[0]+config['settingsPos']['ctrlX'], self.pos_portout[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER)
        self.pos_ipout = (self.osc_block[0], self.osc_block[1]+config['settingsPos']['ipout'])
        self.ipout = wx.TextCtrl(self, value="", pos=(self.pos_ipout[0]+config['settingsPos']['ctrlX'], self.pos_ipout[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER)
        ##ADDRESSES block
        self.pos_choice = (self.addresses_block[0], self.addresses_block[1]+config['settingsPos']['choice'])
        self.choice = wx.Choice(self, pos=(self.pos_choice[0]+config['settingsPos']['choiceX'], self.pos_choice[1]-2), 
                                choices=["List","Seperate"])
        
        self.pos_addr1 = (self.addresses_block[0], self.addresses_block[1]+config['settingsPos']['addr1'])
        self.addr1 = wx.TextCtrl(self, value="", pos=(self.pos_addr1[0]+config['settingsPos']['ctrlX'], self.pos_addr1[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER)
        self.pos_addr2 = (self.addresses_block[0], self.addresses_block[1]+config['settingsPos']['addr2'])
        self.addr2 = wx.TextCtrl(self, value="", pos=(self.pos_addr2[0]+config['settingsPos']['ctrlX'], self.pos_addr2[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER)
        self.pos_addr3 = (self.addresses_block[0], self.addresses_block[1]+config['settingsPos']['addr3'])
        self.addr3 = wx.TextCtrl(self, value="", pos=(self.pos_addr3[0]+config['settingsPos']['ctrlX'], self.pos_addr3[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER)
        self.pos_minmax = (self.addresses_block[0], self.addresses_block[1]+config['settingsPos']['minmax'])
        self.min = wx.TextCtrl(self, value="", pos=(self.pos_minmax[0]+config['settingsPos']['ctrlX'], self.pos_minmax[1]),
                                  size=(30, 20), style=wx.TE_PROCESS_ENTER)
        self.max = wx.TextCtrl(self, value="", pos=(self.pos_minmax[0]+config['settingsPos']['ctrlX']+60, self.pos_minmax[1]),
                                  size=(30, 20), style=wx.TE_PROCESS_ENTER)
        self._setStreamType(wx.EVT_CHOICE)
        
        ##MAPPING block
        self.pos_mag = (self.mapping_block[0], self.mapping_block[1]+config['settingsPos']['mag'])
        self.mag = wx.TextCtrl(self, value="", pos=(self.pos_mag[0]+config['settingsPos']['ctrlX'], self.pos_mag[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER)
        self.pos_rgh = (self.mapping_block[0], self.mapping_block[1]+config['settingsPos']['rgh'])
        self.rgh = wx.TextCtrl(self, value="", pos=(self.pos_rgh[0]+config['settingsPos']['ctrlX'], self.pos_rgh[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER)
        self.pos_act = (self.mapping_block[0], self.mapping_block[1]+config['settingsPos']['act'])
        self.act = wx.TextCtrl(self, value="", pos=(self.pos_act[0]+config['settingsPos']['ctrlX'], self.pos_act[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER)
        
        ##ANALYSIS block
        self.pos_check = (self.analyse_block[0]+config['settingsPos']['check'][0],
                          self.analyse_block[1]+config['settingsPos']['check'][1])
        self.check = wx.CheckBox(self, pos=self.pos_check, style=wx.CHK_2STATE)
        self.check.SetValue(True)
        self.pos_slider = (self.analyse_block[0]+config['settingsPos']['slider'][0],
                           self.analyse_block[1]+config['settingsPos']['slider'][1])
        self.thresh_slider = wx.Slider(self, value=20, minValue=1, maxValue=50,
                                size=config['settingsPos']['sliderSize'], pos=self.pos_slider)
                                  
        self.pos_btn_accept = config['settingsPos']['btn_accept']
        self.btn_accept = wx.Button(self, wx.ID_APPLY, "Apply changes", pos=self.pos_btn_accept)
        self.pos_btn_reset = config['settingsPos']['btn_reset']
        self.btn_reset = wx.Button(self, wx.ID_CLEAR, "Reset", pos=self.pos_btn_reset)
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SCROLL, self._sliderEvt)
        self.Bind(wx.EVT_CHOICE, self._setStreamType)
        self.Bind(wx.EVT_BUTTON, self._apply, id=wx.ID_APPLY)
        self.Bind(wx.EVT_BUTTON, self._reset, id=wx.ID_CLEAR)
        
        self._importUserSettings()
        
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen("#666666", 2))
        dc.SetTextForeground("#AAAAAA")
        
        ##Font titres
        font = wx.Font(config['fontSize']['title'], wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        
        ##Titre OSC
        x, y = self.osc_block
        title_osc = dc.DrawText("OSC PARAMATERS", x, y)
        line_osc = dc.DrawLine(x, y+20, x+190, y+20)
        
        ##Titre addresses
        x, y = self.addresses_block
        title_addresses = dc.DrawText("ADDRESSES (IN)", x, y)
        line_addresses = dc.DrawLine(x, y+20, x+190, y+20)
        
        ##Titre mapping
        x, y = self.mapping_block
        title_mapping = dc.DrawText("MAPPING (OUT)", x, y)
        line_mapping = dc.DrawLine(x, y+20, x+190, y+20)
        
        ##Titre analyse
        x, y = self.analyse_block
        title_analyse = dc.DrawText("ANALYSIS", x, y)
        line_a = dc.DrawLine(x, y+20, x+190, y+20)
        
        ##Font reste
        font = wx.Font(config['fontSize']['body'], wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(font)
        
        ##Texte OSC
        x, y = self.pos_portin
        txt_portin = dc.DrawText("Port in : ", x, y)
        x, y = self.pos_portout
        txt_portout = dc.DrawText("Port out : ", x, y)
        x, y = self.pos_ipout
        txt_ipout = dc.DrawText("IP out : ", x, y)
        
        ##Texte addr
        x, y = self.pos_choice
        txt_choice = dc.DrawText("Stream type : ", x, y)
        x, y = self.pos_addr1
        txt_addr1 = dc.DrawText("Address 1 : ", x, y)
        x, y = self.pos_addr2
        txt_addr2 = dc.DrawText("Address 2 : ", x, y)
        x, y = self.pos_addr3
        txt_addr3 = dc.DrawText("Address 3 : ", x, y)
        
        ##Texte minmax
        x, y = self.pos_minmax
        text_minmax = dc.DrawText("Min / Max : ", x, y+2)
        text_slash = dc.DrawText("/", x+config['settingsPos']['minmaxSep'], y+2)
        
        ##Texte mapping
        x, y = self.pos_mag
        txt_mag = dc.DrawText("Magnitude : ", x, y)
        x, y = self.pos_rgh
        txt_rgh = dc.DrawText("Roughness : ", x, y)
        x, y = self.pos_act
        txt_act = dc.DrawText("Activity : ", x, y)
        
        ##Texte analysis
        x, y = self.pos_check
        txt_check = dc.DrawText("Smoothing (gaussian)", x+20, y+2)
        x, y = self.pos_slider
        txt_thresh = dc.DrawText("Threshold : %d" % self.thresh_slider.GetValue(), x-13, y-20)
        start = dc.DrawText("1", x-13, y-2)
        end = dc.DrawText("50", x+155, y-2)
        
        ##Addresse IP local
        font = wx.Font(config['fontSize']['body']-2, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(font)
        x, y = self.osc_block
        txt_localip = dc.DrawText("Local IP Address : %s" % LOCAL_IP, 
                                   x+config['settingsPos']['localIP'][0], y+config['settingsPos']['localIP'][1])
        
    def _apply(self, evt):
        self._user_settings['portin'] = str(self.portin.GetValue())
        self._user_settings['portout'] = str(self.portout.GetValue())
        self._user_settings['ipout'] = str(self.ipout.GetValue())
        self._user_settings['stream_type'] = self.choice.GetCurrentSelection()
        self._user_settings['addr1'] = str(self.addr1.GetValue())
        self._user_settings['addr2'] = str(self.addr2.GetValue())
        self._user_settings['addr3'] = str(self.addr3.GetValue())
        self._user_settings['min'] = str(self.min.GetValue())
        self._user_settings['max'] = str(self.max.GetValue())
        self._user_settings['map_mag'] = str(self.mag.GetValue())
        self._user_settings['map_rgh'] = str(self.rgh.GetValue())
        self._user_settings['map_act'] = str(self.act.GetValue())
        self._user_settings['smoothing'] = self.check.GetValue()
        self._user_settings['thresh'] = self.thresh_slider.GetValue()
        self._saveParamToFile()
            
    def _importUserSettings(self):
        try:
            f = open(os.path.join(SAVE_PATH, "settings.pref"), 'r')
            for line in f:
                key, value = line.rsplit(':')
                value = value.replace('\n', '')
                if key in ['stream_type','thresh']:
                    value = int(value)
                elif key == 'smoothing':
                    if value == 'True':
                        value = True
                    elif value == 'False':
                        value = False
                self._user_settings[key] = value
            self._initializeSettings('user')
        except IOError, e:
            print "No preferences saved yet..."
            #print "IOError : %s" % str(e)
            self._initializeSettings('default')
        else:
            f.close()

    def _initializeSettings(self, which):
        if which == 'user':
            self.portin.SetValue(self._user_settings['portin'])
            self.portout.SetValue(self._user_settings['portout'])
            self.ipout.SetValue(self._user_settings['ipout'])
            self.choice.SetSelection(self._user_settings['stream_type'])
            self.addr1.SetValue(self._user_settings['addr1'])
            self.addr2.SetValue(self._user_settings['addr2'])
            self.addr3.SetValue(self._user_settings['addr3'])
            self.min.SetValue(self._user_settings['min'])
            self.max.SetValue(self._user_settings['max'])
            self.mag.SetValue(self._user_settings['map_mag'])
            self.rgh.SetValue(self._user_settings['map_rgh'])
            self.act.SetValue(self._user_settings['map_act'])
            self.check.SetValue(self._user_settings['smoothing'])
            self.thresh_slider.SetValue(self._user_settings['thresh'])
            print 'Your preferences have been loaded.'
        elif which == 'default':
            self.portin.SetValue(self._default_settings['portin'])
            self.portout.SetValue(self._default_settings['portout'])
            self.ipout.SetValue(self._default_settings['ipout'])
            self.choice.SetSelection(self._default_settings['stream_type'])
            self.addr1.SetValue(self._default_settings['addr1'])
            self.addr2.SetValue(self._default_settings['addr2'])
            self.addr3.SetValue(self._default_settings['addr3'])
            self.min.SetValue(self._default_settings['min'])
            self.max.SetValue(self._default_settings['max'])
            self.mag.SetValue(self._default_settings['map_mag'])
            self.rgh.SetValue(self._default_settings['map_rgh'])
            self.act.SetValue(self._default_settings['map_act'])
            self.check.SetValue(self._default_settings['smoothing'])
            self.thresh_slider.SetValue(self._default_settings['thresh'])
            print 'Default settings loaded.'
        self._setStreamType(wx.EVT_CHOICE)
        self.Refresh()

    def _reset(self, evt):
        self._initializeSettings('default')

    def _saveParamToFile(self):
        f = open(os.path.join(SAVE_PATH, "settings.pref"), 'w')
        for key in self._user_settings:
            f.write(key+':'+str(self._user_settings[key])+'\n')
        f.close()
        print 'Saved preferences to disk.'
        
    def _sliderEvt(self, evt):
        wx.CallAfter(self.Refresh)

    def _setStreamType(self, evt):
        type = self.choice.GetCurrentSelection()
        user_type = None
        if self._user_settings != {}:
            addr1 = self._user_settings['addr1']
            addr2 = self._user_settings['addr2']
            addr3 = self._user_settings['addr3']
            user_type = self._user_settings['stream_type']
        else:
            addr1 = self._default_settings['addr1']
            addr2 = self._default_settings['addr2']
            addr3 = self._default_settings['addr3']
        
        if type == 0:
            """Type list"""
            if user_type != None and user_type == 1:
                addr1 = "/accxyz"
            self.addr1.SetValue(addr1)
            self.addr2.Enable(False)
            self.addr2.SetBackgroundColour("#555555")
            self.addr2.SetValue("")
            self.addr3.Enable(False)
            self.addr3.SetBackgroundColour("#555555")
            self.addr3.SetValue("")
        elif type == 1:
            """Type seperate"""
            if user_type != None and user_type == 0:
                addr1, addr2, addr3 = "/x", "/y", "/z"
            self.addr1.SetValue(addr1)
            self.addr2.Enable()
            self.addr2.SetBackgroundColour("#FFFFFF")
            self.addr2.SetValue(addr2)
            self.addr3.Enable()
            self.addr3.SetBackgroundColour("#FFFFFF")
            self.addr3.SetValue(addr3)
            
    def getSettings(self):
        temp = {}
        #Sert a convertir les ports en int
        for key in self._user_settings:
            value = self._user_settings[key]
            if key in ['portin','portout','min','max']:
                value = int(value)
            temp[key] = value
        return temp
        
    def hasUserSettings(self):
        if self._user_settings == {}:
            return 0
        else:
            return 1


class RedirectText():
    def __init__(self, textCtrl):
        self.out = textCtrl

    def write(self, string):
        wx.CallAfter(self.out.WriteText, string)

class LogPanel(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos=pos, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        self.SetBackgroundColour("#222222")
        
        log = wx.TextCtrl(self, wx.ID_ANY, size=(size[0]+config['logSize'][0],size[1]+config['logSize'][1]), 
                          pos=config['logPos'], style = wx.TE_MULTILINE|wx.TE_READONLY|wx.NO_BORDER)
        log.SetBackgroundColour("#222222")
        log.SetForegroundColour("#AAAAAA")
        font = wx.Font(config['fontSize']['body'], wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        log.SetFont(font)
        
        redir = RedirectText(log)
        sys.stdout = redir
        sys.stderr = redir
        
        self._initializeSession()
        
    def _initializeSession(self):
        print '\nSession started on : '
        print strftime('%d %b %Y %Hh%M')
        print '-------------------------------'
        
class MonitorPanel(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos=pos, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        self.SetBackgroundColour("#222222")
        
        ##Variables a afficher
        self.raw_x = 0.000
        self.raw_y = 0.000
        self.raw_z = 0.000
        self.mag = 0.000
        self.rgh = 0.000
        self.act = 0.000
        
        ##Positions des blocks
        self.status_block = config['monPos']['status_block']
        self.raw_data_block = config['monPos']['raw_block']
        self.analysis_block = config['monPos']['ana_block']
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
    def OnPaint(self, evt):
        global PRGM_STATE, PRGM_TIME
        
        w, h = self.GetSize()
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen("#666666", 2))
        dc.SetTextForeground("#AAAAAA")
        
        ##Font titres
        font = wx.Font(config['fontSize']['title'], wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        
        ##Titre STATUS
        x, y = self.status_block
        title_status = dc.DrawText("STATUS", x, y)
        line_status = dc.DrawLine(x, y+20, x+190, y+20)
        
        ##Titre RAW DATA
        x, y = self.raw_data_block
        title_raw = dc.DrawText("RAW DATA", x, y)
        line_raw = dc.DrawLine(x, y+20, x+190, y+20)
        
        ##Titre ANALYSIS
        x, y = self.analysis_block
        title_analysis = dc.DrawText("ANALYZED DATA", x, y)
        line_analysis = dc.DrawLine(x, y+20, x+190, y+20)
        
        ##Font reste
        font = wx.Font(config['fontSize']['body'], wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(font)
        
        ##STATUS block
        x, y = self.status_block
        if PRGM_STATE['IS_PLAYING']:
            dc.SetTextForeground("#49A13D")
            play_text = "Currently processing data..."
            play_time = "Total play time : h:%d m:%d s:%d" % calcRunTime(PRGM_TIME['playing'][1], time()+PRGM_TIME['playing'][0])
        else:
            dc.SetTextForeground("#AAAAAA")
            play_text = "Paused"
            play_time = "Total play time : h:%d m:%d s:%d" % calcRunTime(0, PRGM_TIME['playing'][0])
        
        tw, th = dc.GetTextExtent(play_text)
        playtxt = dc.DrawText(play_text, x, y+25)
        playtime = dc.DrawText(play_time, x, y+25+th)

        if PRGM_STATE['IS_RECORDING']:
            dc.SetTextForeground("#C72626")
            rec_text = "Currently recording data..."
            rec_time = "Total rec time : h:%d m:%d s:%d" % calcRunTime(PRGM_TIME['recording'][1], time()+PRGM_TIME['recording'][0])
        else:
            dc.SetTextForeground("#AAAAAA")
            rec_text = "Not recording"
            rec_time = "Total rec time : h:%d m:%d s:%d" % calcRunTime(0, PRGM_TIME['recording'][0])
            
        rectxt = dc.DrawText(rec_text, w/2, y+25)
        rectime = dc.DrawText(rec_time, w/2, y+25+th)
        
        dc.SetTextForeground("#AAAAAA")
        
        ##RAW
        x, y = self.raw_data_block
        rawx = dc.DrawText("X : %.3f" % self.raw_x, x, y+35)
        rawy = dc.DrawText("Y : %.3f" % self.raw_y, x, y+65)
        rawz = dc.DrawText("Z : %.3f" % self.raw_z, x, y+95)
        
        ##ANALYZED
        x, y = self.analysis_block
        mag = dc.DrawText("Magnitude : %.3f" % self.mag, x, y+35)
        rgh = dc.DrawText("Roughness : %.3f" % self.rgh, x, y+65)
        act = dc.DrawText("Activity : %.3f" % self.act, x, y+95)
        
class RecordOptions(wx.Dialog):
    def __init__(self, parent, size, pos=wx.DefaultPosition):
        
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, title="Record Options", pos=pos, size=size)
        self.PostCreate(pre)
        
        if wx.Platform == '__WXMAC__':
            self.SetExtraStyle(wx.DIALOG_EX_METAL)
            
        ##RAW DATA On/Off
        sizer = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Raw data:")
        label.SetHelpText("Records the raw accelerometre data. (x, y, z)")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.choiceRawData = wx.Choice(self, -1, choices=["Off","On"])
        box.Add(self.choiceRawData, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        label = wx.StaticText(self, -1, u"x, y, z axis values (-90\u00b0 to 90\u00b0)")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        
        ##MAX REC time
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Recording time:")
        label.SetHelpText("Maximum recording time for one track.")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.time = wx.TextCtrl(self, -1, "", size=(40,-1))
        self.time.SetHelpText("Maximum recording time for one track.")
        box.Add(self.time, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        label = wx.StaticText(self, -1, "secs.")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 2)
        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL)

        ##SAVE PATH
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Save path:")
        label.SetHelpText("This is where your files will be saved.")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.path = wx.TextCtrl(self, -1, "", size=(300,-1))
        self.path.SetHelpText("This is where your files will be saved.")
        box.Add(self.path, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        
        ##FILE NAME
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "File name:")
        label.SetHelpText("Give a name to your files. Note that the extension will be used.")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.name = wx.TextCtrl(self, -1, "", size=(300,-1))
        self.name.SetHelpText("Give a name to your files. Note that the extension will be used.")
        box.Add(self.name, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        
        ##FILE EXT
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "File name extension:")
        label.SetHelpText(u"Numbers: 'filename1',\u00A0'filename2',\u00A0etc...\nDate and hour: 'filename_Day_Month_Year_Hour:Minutes'")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.choiceFileName = wx.Choice(self, -1, choices=["Numbers","Date and hour"])
        box.Add(self.choiceFileName, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            btnsizer.AddButton(btn)
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)
        
class TransitionPanel(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos=pos, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        self.SetBackgroundColour("#222222")

class HelpDialog(wx.MiniFrame):
    def __init__(self, parent, title="Help", pos=wx.DefaultPosition, size=(400,300),
                 style=wx.DEFAULT_FRAME_STYLE):
        wx.MiniFrame.__init__(self, parent, -1, title, pos, size, style)
        panel = wx.Panel(self, -1, size=size)
        panel.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        panel.SetBackgroundColour("#222222")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        title = wx.StaticText(panel, label="\nACC Data Analyzer help\n")
        title.SetForegroundColour("#AAAAAA")
        sizer.Add(title, 0, wx.ALIGN_CENTER)
        
        description = wx.StaticText(panel, 
                      label=HELP_TEXT['general'],
                      size=(self.GetSize()[0]-10,150), pos=(5,0))
        description.SetForegroundColour("#AAAAAA")
        sizer.Add(description, 0, wx.ALIGN_CENTER)
        
        button = wx.Button(panel, -1, "Close")
        sizer.Add(button, 0, wx.ALIGN_CENTER)
        
        panel.SetSizer(sizer)
        self.Bind(wx.EVT_BUTTON, self.OnCloseMe, button)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def OnCloseMe(self, event):
        self.Close(True)

    def OnCloseWindow(self, event):
        self.Destroy()

if __name__ == '__main__':
    from _core import *
    from pyo import Server
    
    server = Server(sr=SAMP_RATE, buffersize=BUFFER_SIZE).boot().start()

    app = wx.App(False)

    provider = wx.SimpleHelpProvider()
    wx.HelpProvider.Set(provider)
    wx.ArtProvider.Push(AccArtProvider())
    wx.ArtProvider.Push(PlayerArtProvider())

    size = (50,46)
    tabs = [
        ('Settings', wx.ArtProvider.GetBitmap(ID_BTN_SETTINGS, size=size)),
        ('Log', wx.ArtProvider.GetBitmap(ID_BTN_LOG, size=size)),
        ('Monitor', wx.ArtProvider.GetBitmap(ID_BTN_MONITOR, size=size)),
        ('Sep', wx.ArtProvider.GetBitmap(ID_SEP, size=(2,50))),
        ('Start', wx.ArtProvider.GetBitmap(ID_BTN_START, size=size)),
        ('Pause', wx.ArtProvider.GetBitmap(ID_BTN_PAUSE, size=size)),
        ('Rec', wx.ArtProvider.GetBitmap(ID_BTN_REC, size=size)),
        ('Sep', wx.ArtProvider.GetBitmap(ID_SEP, size=(2,50))),
        ('Save', wx.ArtProvider.GetBitmap(ID_BTN_SAVE, size=size)),
        ('Player', wx.ArtProvider.GetBitmap(ID_BTN_PLAYER, size=size))
    ]
    fstyle = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX)
    
    ##Importation des grandeurs de cadres
    size_settings = config['panelSize']['settings']
    size_logpanel = config['panelSize']['log']
    size_monitorpanel = config['panelSize']['mon']
    size_transitionpanel = config['panelSize']['transition']
    
    frame = MainFrame(None, title="ACC Data Analyzer", pos=(100,100), size=config['panelSize']['init'], style=fstyle)
    frame.CreateTabs(tabs)

    objects_list = []

    #TABS Panels
    log_panel = LogPanel(frame, (0,0), size_logpanel)
    settings_panel = SettingsPanel(frame, (0,0), size_settings)
    monitor_panel = MonitorPanel(frame, (0,0), size_monitorpanel)
    transition_panel = TransitionPanel(frame, (0,0), size_transitionpanel)

    #INIT
    settings_panel.Show()
    log_panel.Show(False)
    transition_panel.Show(False)
    monitor_panel.Show(False)

    def OnTabChange(tabIndex):
        global time_playing, time_recording, objects_list
        
        if tabIndex == 0:
            transition_panel.Show()
            log_panel.Show(False)
            monitor_panel.Show(False)
            frame.changeSize(size_settings)
            settings_panel.Show()
            transition_panel.Show(False)
        elif tabIndex == 1:
            transition_panel.Show()
            settings_panel.Show(False)
            monitor_panel.Show(False)
            frame.changeSize(size_logpanel)
            log_panel.Show()
            transition_panel.Show(False)
        elif tabIndex == 2:
            transition_panel.Show()
            log_panel.Show(False)
            settings_panel.Show(False)
            frame.changeSize(size_monitorpanel)
            monitor_panel.Show()
            transition_panel.Show(False)
        elif tabIndex == ITEM_START:
            """Bouton play"""
            if not IS_READY:
                if createObjects():
                    ##simule l'appui sur le bouton start
                    event = wx.CommandEvent(winid=ITEM_START)
                    if wx.Platform == '__WXMAC__':
                        frame.OnToolBarMacNative(event)
                    else:
                        frame.OnToolBarDefault(event)
            else:
                time_playing[1] = time()
                for i in range(3):
                    objects_list[i].play()
        elif tabIndex == ITEM_PAUSE:
            """Bouton pause"""
            time_playing[2] = time()
            time_playing[0] += time_playing[2]-time_playing[1]
            time_playing[1] = 0.
            if time_recording[1] != 0:
                time_recording[2] = time()
                time_recording[0] += time_recording[2]-time_recording[1]
                time_recording[1] = 0.
            for i in range(3):
                objects_list[i].stop()
        elif tabIndex == ITEM_REC:
            """Bouton rec"""
            if not IS_READY:
                if createObjects():
                    ##simule l'appui sur record pour commencer l'enregistrement
                    event = wx.CommandEvent(winid=ITEM_REC)
                    if wx.Platform == '__WXMAC__':
                        frame.OnToolBarMacNative(event)
                    else:
                        frame.OnToolBarDefault(event)
                    time_playing[1] = time()
            else:
                if IS_RECORDING:
                    time_recording[1] = time()
                else:
                    time_recording[2] = time()
                    time_recording[0] += time_recording[2]-time_recording[1]
                    time_recording[1] = 0.
        elif tabIndex == ITEM_SAVE:
            """Bouton save"""
            pass
        elif tabIndex == ITEM_PLAYER:
            """Buton open"""
            pass
        
    def createObjects():
        global objects_list, IS_READY
        if settings_panel.hasUserSettings():
            settings = settings_panel.getSettings()
            if settings['stream_type'] == 0:
                address = settings['addr1']
            else:
                address = [settings['addr1'], settings['addr2'], settings['addr3']]
            r_obj = AccDataReceiver(settings['portin'], address, settings['min'], settings['max'], settings['smoothing'])
            a_obj = AccDataAnalyser(r_obj, settings['thresh'])
            mapping = {'x':"/accx",
                       'y':"/accy",
                       'z':"/accz",
                       'mag':settings['map_mag'],
                       'rgh':settings['map_rgh'],
                       'act':settings['map_act']}
            s_obj = AccDataSend(r_obj, a_obj, settings['portout'], settings['ipout'], mapping)
            options = frame.getRecOptions()
            rec_obj = RecordModule(frame, r_obj, a_obj, options['rec_time'], options['raw_data'], options['file_ext'])
            objects_list = [r_obj, a_obj, s_obj, rec_obj]
            frame.rec_module = objects_list[3]
            IS_READY = True
            print "All objects created. Now running."
            return 1
        else:
            print "< WARNING >\nYou need to click on 'Apply changes' in the settings panel before starting the process."
            event = wx.CommandEvent(winid=1)
            if wx.Platform == '__WXMAC__':
                frame.OnToolBarMacNative(event)
            else:
                frame.OnToolBarDefault(event)
            return 0

    def updateMonitor():
        while IS_RUNNING:
            if monitor_panel.IsShown() and objects_list != []:
                monitor_panel.raw_x = objects_list[0]['x'].get()
                monitor_panel.raw_y = objects_list[0]['y'].get()
                monitor_panel.raw_z = objects_list[0]['z'].get()
                monitor_panel.mag = objects_list[1]['mag'].get()
                monitor_panel.rgh = objects_list[1]['rgh'].get()
                monitor_panel.act = objects_list[1]['act'].get()
                wx.CallAfter(monitor_panel.Refresh)
            sleep(.1)
            
    monitor_thread = threading.Thread(target=updateMonitor, args=())
    monitor_thread.start()
    frame.thread = monitor_thread
    frame.audio_server = server
    frame.OnTabChange = OnTabChange
    frame.fctSave = settings_panel._apply
    #server.gui(locals())
    frame.Show()
    app.MainLoop()
