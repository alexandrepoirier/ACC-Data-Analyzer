#!/usr/bin/env python
# encoding: utf-8

"""
Acc Data Analyzer - main.py
Alexandre Poirier

Dernières modifications : mardi 8 avril 2014.
"""

import wx
import threading
from _core import *
from _interface_multi import *
from time import sleep, time
from pyo import Server

server = Server(sr=SAMP_RATE, buffersize=BUFFER_SIZE).boot().start()

app = wx.App(False)

help_provider = wx.SimpleHelpProvider()
wx.HelpProvider.Set(help_provider)
#A supprimer eventuellement
#wx.ArtProvider.Push(AccArtProvider())
#wx.ArtProvider.Push(PlayerArtProvider())

size = (50,50) if wx.Platform == '__WXMAC__' else (30,30)
tabs = [
    ('Settings', catalog['icn_settings'].getBitmap()),
    ('Log', catalog['icn_log'].getBitmap()),
    ('Monitor', catalog['icn_monitor'].getBitmap()),
    ('Sep', catalog['icn_sep'].getBitmap()),
    ('Start', catalog['icn_start'].getBitmap()),
    ('Pause', catalog['icn_pause'].getBitmap()),
    ('Rec', catalog['icn_rec'].getBitmap()),
    ('Sep', catalog['icn_sep'].getBitmap()),
    ('Save', catalog['icn_save'].getBitmap()),
    ('Player', catalog['icn_player'].getBitmap())
]
fstyle = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX)

##Importation des grandeurs de cadres
size_settings = config['panelSize']['settings']
size_logpanel = config['panelSize']['log']
size_monitorpanel = config['panelSize']['mon']
size_transitionpanel = config['panelSize']['transition']

frame = MainFrame(None, title="ACC Data Analyzer", pos=(100,100), size=config['panelSize']['init'], style=fstyle)
frame.CreateTabs(tabs)

#liste qui contiendra tous les objets audio
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
    global PRGM_TIME, objects_list
    
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
        if not PRGM_STATE['IS_READY']:
            if createObjects():
                ##simule l'appui sur le bouton start
                event = wx.CommandEvent(winid=ITEM_START)
                if wx.Platform == '__WXMAC__':
                    frame.OnToolBarMacNative(event)
                else:
                    frame.OnToolBarDefault(event)
        else:
            PRGM_TIME['playing'][1] = time()
            for i in range(3):
                objects_list[i].play()
    elif tabIndex == ITEM_PAUSE:
        """Bouton pause"""
        PRGM_TIME['playing'][2] = time()
        PRGM_TIME['playing'][0] += PRGM_TIME['playing'][2]-PRGM_TIME['playing'][1]
        PRGM_TIME['playing'][1] = 0.
        if PRGM_TIME['recording'][1] != 0:
            PRGM_TIME['recording'][2] = time()
            PRGM_TIME['recording'][0] += PRGM_TIME['recording'][2]-PRGM_TIME['recording'][1]
            PRGM_TIME['recording'][1] = 0.
        for i in range(3):
            objects_list[i].stop()
    elif tabIndex == ITEM_REC:
        """Bouton rec"""
        if not PRGM_STATE['IS_READY']:
            if createObjects():
                ##simule l'appui sur record pour commencer l'enregistrement
                event = wx.CommandEvent(winid=ITEM_REC)
                if wx.Platform == '__WXMAC__':
                    frame.OnToolBarMacNative(event)
                else:
                    frame.OnToolBarDefault(event)
                PRGM_TIME['playing'][1] = time()
        else:
            if PRGM_STATE['IS_RECORDING']:
                PRGM_TIME['recording'][1] = time()
            else:
                PRGM_TIME['recording'][2] = time()
                PRGM_TIME['recording'][0] += PRGM_TIME['recording'][2]-PRGM_TIME['recording'][1]
                PRGM_TIME['recording'][1] = 0.
    elif tabIndex == ITEM_SAVE:
        """Bouton save"""
        pass
    elif tabIndex == ITEM_PLAYER:
        """Buton open"""
        pass
    
def createObjects():
    global objects_list, PRGM_STATE
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
        PRGM_STATE['IS_READY'] = True
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
    while PRGM_STATE['IS_RUNNING']:
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

#liens entre interface et deroulement principal
frame.thread = monitor_thread
frame.audio_server = server
frame.OnTabChange = OnTabChange
frame.fctSave = settings_panel._apply

frame.Show()
app.MainLoop()