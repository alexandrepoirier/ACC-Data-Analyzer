#!/usr/bin/env python
# encoding: utf-8

"""
Dernières modifications : mardi 8 avril 2014

À faire:
    - Faire en sorte que si la session en cours a été ouverte à partir
      d'un fichier, la fonction de sauvegarde écrase automatiquement
      l'ancienne version du fichier, sans rouvrir la fenêtre de
      sauvegarde.
    - Actualiser les linkId de tous les items lors de la suppression d'items
      ou de changements de positions.
    - À l'ouverture, présenter un splash screen avec comme options de pouvoir
      créer une nouvelle session ou d'en ouvrir une.
Notes:
    - Comportement étrange... le dictionnaire _user_settings du player change
      le type de 'portout' de int vers str pour une raison quelconque...
      La valeur est ajustée à chaque fois que l'usagé modifie le champ de texte
      associé, mais aucune autre opération n'est effectué sur le dictionnaire
      entre cette écriture et l'extraction de la donnée pour utilisation finale.
"""

import wx
import wx.lib.agw.ultimatelistctrl as ULC
import sys
import os
import copy
from _core import AccDataPlayer
from pyo import *

HOME_PATH = os.path.expanduser("~")
SAVE_PATH = os.path.join(HOME_PATH, "Documents", "AccData")

##Import icones perso (PyEmbeddedImage)
if wx.Platform == '__WXMAC__':
    from Ressources.img.mac_icons import catalog
else:
    from Ressources.img.default_icons import catalog

#A supprimer eventuellement
##Constantes pour icones perso
#ID_BTN_START = "01"
#ID_BTN_PAUSE = "02"
#ID_BTN_ADD = "10"
#ID_BTN_NEW = "11"
#ID_BTN_OPEN = "12"
#ID_BTN_SAVE = "07"
#ID_SEP = "08"

ITEM_START = 30
ITEM_PAUSE = 40

##Dictionnaire des variables d'etat du player
PLAYER_STATE = {'IS_READY':False, 'IS_SAVED':False}
            
wildcard_accdata = "Wave files (*.wav/*.wave)|*.wav;*.wave|"\
                   "AIFF files (*.aif/*.aiff)|*.aif;*.aiff|"\
                   "FLAC files (*.flac)|*.flac|"\
                   "Ogg file (*.ogg)|*.ogg"
wildcard_session = "Session file (*.acc)|*.acc"

#A supprimer eventuellement
#class PlayerArtProvider(wx.ArtProvider):
#    def __init__(self):
#        wx.ArtProvider.__init__(self)

#    def CreateBitmap(self, artid, client, size):
#        bmp = wx.NullBitmap
#        if artid == ID_BTN_START:
#            bmp = wx.Bitmap(ART_BTN_START, wx.BITMAP_TYPE_PNG)
#            bmp.SetSize(size)
#        elif artid == ID_BTN_PAUSE:
#            bmp = wx.Bitmap(ART_BTN_PAUSE, wx.BITMAP_TYPE_PNG)
#            bmp.SetSize(size)
#        elif artid == ID_BTN_ADD:
#            bmp = wx.Bitmap(ART_BTN_ADD, wx.BITMAP_TYPE_PNG)
#            bmp.SetSize(size)
#        elif artid == ID_BTN_NEW:
#            bmp = wx.Bitmap(ART_BTN_NEW, wx.BITMAP_TYPE_PNG)
#            bmp.SetSize(size)
#        elif artid == ID_BTN_OPEN:
#            bmp = wx.Bitmap(ART_BTN_OPEN, wx.BITMAP_TYPE_PNG)
#            bmp.SetSize(size)
#        elif artid == ID_SEP:
#            bmp = wx.Bitmap(ART_SEP, wx.BITMAP_TYPE_PNG)
#            bmp.SetSize(size)
#        elif artid == ID_BTN_SAVE:
#            bmp = wx.Bitmap(ART_BTN_SAVE, wx.BITMAP_TYPE_PNG)
#            bmp.SetSize(size)
#        return bmp

class MySearchCtrl(wx.SearchCtrl):
    maxSearches = 5
    
    def __init__(self, parent, id=-1, value="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 doSearch=None):
        style |= wx.TE_PROCESS_ENTER
        wx.SearchCtrl.__init__(self, parent, id, value, pos, size, style)
        self.ShowCancelButton(True)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEntered)
        self.Bind(wx.EVT_MENU_RANGE, self.OnMenuItem, id=1, id2=self.maxSearches)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel, self)
        self.doSearch = doSearch
        self.searches = []

    def OnCancel(self, evt):
        self.Clear()
        evt.Skip()
    
    def OnTextEntered(self, evt):
        text = self.GetValue()
        if self.doSearch(text):
            self.searches.append(text)
            if len(self.searches) > self.maxSearches:
                del self.searches[0]
            self.SetMenu(self.MakeMenu())            
        self.SetValue("")

    def OnMenuItem(self, evt):
        text = self.searches[evt.GetId()-1]
        self.doSearch(text)
        
    def MakeMenu(self):
        menu = wx.Menu()
        item = menu.Append(-1, "Recent Searches")
        item.Enable(False)
        for idx, txt in enumerate(self.searches):
            menu.Append(1+idx, txt)
        return menu

class PlayerFrame(wx.Frame):
    def __init__(self, parent=None, title="", pos=wx.DefaultPosition, size=wx.DefaultSize):
        pos, size = self._getWindowPosSize(pos, size)
        wx.Frame.__init__(self, parent, -1, title, pos, size)
        self.SetMinSize((778,450))
        statusbar = self.CreateStatusBar()
        statusbar.SetFieldsCount(4)
        statusbar.SetStatusWidths([100,200,70,200])
        self.SetStatusText("Stopped", 0)
        
        self.SetStatusText("Progress : ", 2)
        self.gauge = wx.Gauge(statusbar, -1, size=(150,-1))
        rect = statusbar.GetFieldRect(3)
        self.gauge.SetPosition((rect.x+2, rect.y+2))
              
        ##Liste de listes : [[index, path, time],[...]]
        self.file_list = []
        ##Liste de listes : [[index, path, time, [repeats,objId], [state,objId], [type,objId], linkId],[...]]
        ##linkId = -1 -> pas de link, sinon le id de l'item joint est inscrit
        self.play_list = []
        ##Titre de la session en cours
        self.sessionTitle = ""
        self.windowTitle = "ACC Data Player"
        self._newSessionTitle()
        
        ##Creation du dossier de sauvegarde, si necessaire
        self._createFolder(SAVE_PATH)
        
        self._user_settings = {'ipout':"127.0.0.1",'portout':8001,
                               'mag':"/acc/mag",'rgh':"/acc/rgh",'act':"/acc/act",
                               'x':"/acc/raw/x",'y':"/acc/raw/y",'z':"/acc/raw/z"}
                               
        self._player = None
        
        ##################
        ## TOOLBAR init ##
        ##################
        TBFLAGS = wx.TB_HORIZONTAL|wx.NO_BORDER|wx.TB_FLAT
        self.toolbar = self.CreateToolBar(TBFLAGS)
        
        new_bmp =  catalog['icn_new'].GetBitmap()
        save_bmp = catalog['icn_save'].GetBitmap()
        open_bmp = catalog['icn_open'].GetBitmap()
        play_bmp = catalog['icn_start'].GetBitmap()
        pause_bmp= catalog['icn_pause'].GetBitmap()
        add_bmp = catalog['icn_add'].GetBitmap()
        sep_bmp = catalog['icn_sep'].GetBitmap()
        icn_size = (50,50) if wx.Platform == '__WXMAC__' else (30,30)
        self.toolbar.SetToolBitmapSize(icn_size)
        
        ##NEW tool
        self.toolbar.AddLabelTool(10, "New", new_bmp, shortHelp="New", longHelp="Create new session.")
        self.Bind(wx.EVT_TOOL, self._OnNewTool, id=10)
        
        self.toolbar.AddLabelTool(60, "Save", save_bmp, shortHelp="Save", longHelp="Save the ongoing session.")
        self.Bind(wx.EVT_TOOL, self._OnSaveTool, id=60)

        ##OPEN tool
        self.toolbar.AddLabelTool(20, "Open", open_bmp, shortHelp="Open", longHelp="Open previously saved session.")
        self.Bind(wx.EVT_TOOL, self._OnOpenTool, id=20)

        ##SEP
        self.toolbar.AddSimpleTool(1, bitmap=sep_bmp)
        self.toolbar.EnableTool(1, False)
        
        ##ADD tool
        self.toolbar.AddLabelTool(50, "Add", add_bmp, shortHelp="Add", longHelp="Add files to the 'Files' list.")
        self.Bind(wx.EVT_TOOL, self._OnAddTool, id=50)
        
        ##PLAY tool
        self.toolbar.AddLabelTool(ITEM_START, "Start", play_bmp, shortHelp="Start", longHelp="Start reading the Playlist.")
        self.Bind(wx.EVT_TOOL, self._OnStartTool, id=30)

        ##PAUSE tool
        self.toolbar.AddLabelTool(ITEM_PAUSE, "Pause", pause_bmp, shortHelp="Pause", longHelp="Stop reading the Playlist.")
        self.Bind(wx.EVT_TOOL, self._OnPauseTool, id=40)
        
        ##SEP
        self.toolbar.AddSimpleTool(3, bitmap=sep_bmp)
        self.toolbar.EnableTool(3, False)
        
        ##OPTIONS
        text = wx.StaticText(self.toolbar, label="Port out :")
        self.toolbar.AddControl(text)
        self.portout_ctrl = wx.TextCtrl(self.toolbar, id=wx.ID_ANY, value=str(self._user_settings['portout']), size=(70,-1))
        self.Bind(wx.EVT_TEXT, self._portoutChange, self.portout_ctrl)
        self.toolbar.AddControl(self.portout_ctrl)
        
        text = wx.StaticText(self.toolbar, label="IP out :")
        self.toolbar.AddControl(text)
        self.ipout_ctrl = wx.TextCtrl(self.toolbar, id=wx.ID_ANY, value=self._user_settings['ipout'], size=(100,-1))
        self.Bind(wx.EVT_TEXT, self._ipoutChange, self.ipout_ctrl)
        self.toolbar.AddControl(self.ipout_ctrl)
        
        ##SEP
        self.toolbar.AddSimpleTool(2, bitmap=sep_bmp)
        self.toolbar.EnableTool(2, False)
        
        ##SERACH ctrl
        self.search = MySearchCtrl(self.toolbar, size=(200,-1), doSearch=self._DoSearch)
        self.toolbar.AddControl(self.search)
        
        self.toolbar.Realize()
        ##initialise le bouton pause a desactive...
        self.toolbar.EnableTool(40, False)

        #########################
        ## Creation du menubar ##
        #########################
        menubar = wx.MenuBar()
        
        filemenu = wx.Menu()
        saveitem = filemenu.Append(100, "Save Session\tCtrl+S","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._OnSaveTool, id=100)
        
        openitem = filemenu.Append(101, "Open Session\tCtrl+O","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._OnOpenTool, id=101)
        
        optionsitem = filemenu.Append(103, "Mapping\tCtrl+Alt+O","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._mappingDlg, id=103)
        
        quititem = filemenu.Append(102,"Quit\tCtrl+Q","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU,self._onQuit, id=102)
        self.Bind(wx.EVT_CLOSE,self._onQuit)
        menubar.Append(filemenu, "&File")
        
        actionmenu = wx.Menu()
        startitem = actionmenu.Append(200, "Start\tCtrl+Shift+S","",wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self._menuStart, id=200)
        
        additem = actionmenu.Append(201, "Add file\tCtrl+Shift+A","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._OnAddTool, id=201)
        
        transferitem = actionmenu.Append(202, "Add to list\tCtrl+D","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._addToPlaylist, id=202)
        
        moveupitem = actionmenu.Append(203, "Move up\tCtrl+UP","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU,self._moveItemPlaylistUP, id=203)
        
        movedownitem = actionmenu.Append(204, "Move down\tCtrl+DOWN","",wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU,self._moveItemPlaylistDOWN, id=204)
        menubar.Append(actionmenu, "&Action")
        
        self.SetMenuBar(menubar)
        
        ############################
        ## Creation des controles ##
        ############################
        self.panel = wx.Panel(self, -1, pos=(0,0), size=size)
        self.panel.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        self.panel.SetBackgroundColour("#333334")
        
        titleFont = wx.Font(14, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        
        bottomWeigh = 9
        leftWeigh = 3
        rightWeigh = 7
        
        ##Sizer principal / vertical
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer((0,10))
        
        ##Library titre et boutons
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer((10,0))
        
        boxbtn = wx.BoxSizer(wx.HORIZONTAL)
        title = wx.StaticText(self.panel, label="Library")
        title.SetForegroundColour("#FFFFFF")
        title.SetFont(titleFont)
        boxbtn.Add(title, 0, wx.ALIGN_BOTTOM)
        boxbtn.AddSpacer((3,0))
        btnremove = wx.BitmapButton(self.panel, -1, catalog['icn_remove'].GetBitmap(), 
                                    (12, 12), style = wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self._removeItemFileList, btnremove)
        boxbtn.Add(btnremove, 0, wx.ALIGN_BOTTOM)
        btnaddto = wx.BitmapButton(self.panel, -1, catalog['icn_addto'].GetBitmap(), 
                                    (12, 12), style = wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self._addToPlaylist, btnaddto)
        boxbtn.Add(btnaddto, 0, wx.ALIGN_BOTTOM)
        box.Add(boxbtn, leftWeigh, wx.ALIGN_BOTTOM)
        
        ##Playlist titre
        box.AddSpacer((10,0))
        
        boxbtn = wx.BoxSizer(wx.HORIZONTAL)
        title = wx.StaticText(self.panel, label="Playlist")
        title.SetForegroundColour("#FFFFFF")
        title.SetFont(titleFont)
        boxbtn.Add(title, 0, wx.ALIGN_BOTTOM)
        boxbtn.AddSpacer((3,0))
        ##bouton pour supprimer
        btnremove = wx.BitmapButton(self.panel, -1, catalog['icn_remove'].GetBitmap(), 
                                    (12, 12), style = wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self._removeItemPlaylist, btnremove)
        boxbtn.Add(btnremove, 0, wx.ALIGN_BOTTOM)
        ##bouton pour deplacer vers le haut
        btnmoveup = wx.BitmapButton(self.panel, -1, catalog['icn_up'].GetBitmap(), 
                                    (12, 12), style = wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self._moveItemPlaylistUP, btnmoveup)
        boxbtn.Add(btnmoveup, 0, wx.ALIGN_BOTTOM)
        ##bouton pour deplacer vers le bas
        btnmovedown = wx.BitmapButton(self.panel, -1, catalog['icn_down'].GetBitmap(), 
                                    (12, 12), style = wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self._moveItemPlaylistDOWN, btnmovedown)
        boxbtn.Add(btnmovedown, 0, wx.ALIGN_BOTTOM)
        ##bouton pour unir deux fichiers
        btnlink = wx.BitmapButton(self.panel, -1, catalog['icn_link'].GetBitmap(), 
                                    (12, 12), style = wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self._linkItems, btnlink)
        boxbtn.Add(btnlink, 0, wx.ALIGN_BOTTOM)
        
        box.Add(boxbtn, rightWeigh, wx.ALIGN_BOTTOM)
        sizer.Add(box, 0, wx.EXPAND)
        
        ##Ligne files
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer((10,0))
        fullLine = ""
        for i in range(300): fullLine += u"\xaf"
        line = wx.StaticText(self.panel, label=fullLine)
        line.SetForegroundColour("#AAAAAA")
        box.Add(line, leftWeigh, wx.ALIGN_TOP)
        ##Ligne playlit
        box.AddSpacer((10,0))
        line = wx.StaticText(self.panel, label=fullLine)
        line.SetForegroundColour("#AAAAAA")
        box.Add(line, rightWeigh, wx.ALIGN_TOP)
        box.AddSpacer((10,0))
        sizer.Add(box, 0, wx.EXPAND)

        ##Library List Ctrl - matiere
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer((10,0))
        self.fileListCtrl = wx.ListCtrl(self.panel, -1, size=(200,300), style=wx.LC_REPORT|wx.BORDER_THEME)
        self.fileListCtrl.SetBackgroundColour("#222222")
        self.fileListCtrl.SetForegroundColour("#1485CC")
        self.fileListCtrl.InsertColumn(0, "Name")
        self.fileListCtrl.InsertColumn(1, "Time", wx.LIST_FORMAT_RIGHT)
            
        self.fileListCtrl.SetColumnWidth(0, 220)
        self.fileListCtrl.SetColumnWidth(1, 60)
        
        box.Add(self.fileListCtrl, leftWeigh, wx.EXPAND)
        box.AddSpacer((10,0))
        
        ##Playlist Ctrl
        self.playListCtrl = ULC.UltimateListCtrl(self.panel, wx.ID_ANY, size=(300,300), style=wx.BORDER_THEME, agwStyle=wx.LC_REPORT | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._OnPlaylistSelect)
        self.playListCtrl.SetBackgroundColour("#222222")
        self.playListCtrl.SetForegroundColour("#00B233")
        self.playListCtrl.InsertColumn(0, "Name")
        self.playListCtrl.InsertColumn(1, "Time", wx.LIST_FORMAT_RIGHT)
        self.playListCtrl.InsertColumn(2, "Repeats", wx.LIST_FORMAT_RIGHT)
        self.playListCtrl.InsertColumn(3, "Play", wx.LIST_FORMAT_RIGHT)
        self.playListCtrl.InsertColumn(4, "Type", wx.LIST_FORMAT_RIGHT)
            
        self.playListCtrl.SetColumnWidth(0, 300)
        self.playListCtrl.SetColumnWidth(1, 60)
        self.playListCtrl.SetColumnWidth(2, 80)
        self.playListCtrl.SetColumnWidth(3, 60)
        self.playListCtrl.SetColumnWidth(4, 130)
        
        box.Add(self.playListCtrl, rightWeigh, wx.EXPAND)
        box.AddSpacer((10,0))
        sizer.Add(box, bottomWeigh, wx.EXPAND)
        sizer.AddSpacer((0,10))
        
        self.panel.SetSizer(sizer)
        
    #####################################
    ##            Methodes             ##
    ## Classees par ordre alphabetique ##
    #####################################
    def _addFileInCtrl(self):
        if wx.Platform == '__WXMSW__':
            slash = self.file_list[-1][0].rfind("\\")+1
        else:
            slash = self.file_list[-1][0].rfind("/")+1
        index = self.fileListCtrl.InsertStringItem(sys.maxint, self.file_list[-1][0][slash:])
        self.fileListCtrl.SetStringItem(index, 1, self.file_list[-1][1])
        self.file_list[-1].insert(0,index)
        self.fileListCtrl.Update()

    def _addToPlaylist(self, evt):
        self.gauge.Pulse()
        wx.Yield()
        indices = [self.fileListCtrl.GetFirstSelected()]
        while indices[-1] != -1:
            indices.append(self.fileListCtrl.GetNextSelected(indices[-1]))
        del indices[-1]
        self._createPlaylistItems(indices)
        self._markUnsaved()
    
    def _changeRepeats(self, evt):
        id = evt.GetId()
        obj = evt.GetEventObject()
        for i in range(len(self.play_list)):
            if self.play_list[i][3][1] == id:
                self.play_list[i][3][0] = obj.GetValue()
                break
        self._markUnsaved()
    
    def _checkPlay(self, evt):
        id = evt.GetId()
        obj = evt.GetEventObject()
        for i in range(len(self.play_list)):
            if self.play_list[i][4][1] == id:
                self.play_list[i][4][0] = obj.GetValue()
                break
        self._markUnsaved()
        
    def _createFolder(self, path):
        if not os.path.exists(path): 
            os.makedirs(path)
    
    def _createPlaylistFromFile(self):
        for i in range(len(self.play_list)):
            data = self.play_list[i]
            
            ##nom du fichier
            if wx.Platform == '__WXMSW__':
                slash = data[0].rfind("\\")+1
            else:
                slash = data[0].rfind("/")+1
            name = data[0][slash:]
            if self.play_list[i][5] != -1: name += " (linked)"
            index = self.playListCtrl.InsertStringItem(sys.maxint, name)
            data.insert(0,index)
            
            ##spinctrl / nb de lectures
            self.playListCtrl.SetStringItem(index, 1, data[2])
            sc = wx.SpinCtrl(self.playListCtrl, -1, size=(60, -1))
            sc.SetRange(1,100)
            sc.SetValue(data[3])
            data[3] = [data[3],sc.GetId()]
            self.Bind(wx.EVT_SPINCTRL, self._changeRepeats, sc)
            self.playListCtrl.SetItemWindow(index, 2, sc)
            
            ##checkbox / state
            checkBox = wx.CheckBox(self.playListCtrl, -1)
            checkBox.SetValue(data[4])
            data[4] = [data[4],checkBox.GetId()]
            self.Bind(wx.EVT_CHECKBOX, self._checkPlay, checkBox)
            self.playListCtrl.SetItemWindow(index, 3, checkBox)
            
            choice = wx.Choice(self.playListCtrl, -1, choices=["Analyzed", "Raw"])
            choice.SetSelection(data[5])
            data[5] = [data[5],choice.GetId()]
            self.Bind(wx.EVT_CHOICE, self._setItemType, choice)
            self.playListCtrl.SetItemWindow(index, 4, choice)
    
    def _createPlaylistItems(self, items):
        for i in range(len(items)):
            data = copy.copy(self.file_list[items[i]])
            
            ##nom du fichier
            if wx.Platform == '__WXMSW__':
                slash = data[1].rfind("\\")+1
            else:
                slash = data[1].rfind("/")+1
            index = self.playListCtrl.InsertStringItem(sys.maxint, data[1][slash:])
            data[0] = index
            
            ##spinctrl / nb de lectures
            self.playListCtrl.SetStringItem(index, 1, data[2])
            sc = wx.SpinCtrl(self.playListCtrl, -1, size=(60, -1))
            data.append([1,sc.GetId()]) #Repeats
            sc.SetRange(1,100)
            sc.SetValue(data[3][0])
            self.Bind(wx.EVT_SPINCTRL, self._changeRepeats, sc)
            self.playListCtrl.SetItemWindow(index, 2, sc)
            
            ##checkbox / state
            checkBox = wx.CheckBox(self.playListCtrl, -1)
            data.append([True,checkBox.GetId()]) #Item state on/off
            checkBox.SetValue(data[4][0])
            self.Bind(wx.EVT_CHECKBOX, self._checkPlay, checkBox)
            self.playListCtrl.SetItemWindow(index, 3, checkBox)
            
            ##choice / type
            choice = wx.Choice(self.playListCtrl, -1, choices=["Analyzed", "Raw"])
            ##on cherche pour le mot raw dans le titre du fichier
            if data[1].lower().find("raw") != -1:
                choice.SetSelection(1)
                data.append([1,choice.GetId()])
            else:
                data.append([0,choice.GetId()])
            self.Bind(wx.EVT_CHOICE, self._setItemType, choice)
            self.playListCtrl.SetItemWindow(index, 4, choice)
            
            data.append(-1) #linkId = -1 par defaut
            self.play_list.append(data)
        self.gauge.SetValue(0)
    
    def _createPlayer(self, offset=0):
        self._player = AccDataPlayer(self._getFinalPlaylist(), int(self._user_settings['portout']),
                                      self._user_settings['ipout'], self._makeMappingDict(), offset=offset)
        self._end_trig = TrigFunc(self._player['end'], self._finishedPlaying)
        self._snd_trig = TrigFunc(self._player['snd'], self._updateTrackPlaying)
        
    def _deselectAll(self):
        indices = [self.fileListCtrl.GetFirstSelected()]
        while indices[-1] != -1:
            indices.append(self.fileListCtrl.GetNextSelected(indices[-1]))
        del indices[-1]
        
        for i in range(len(indices)):
            self.fileListCtrl.Select(indices[i], on=0)
            
    def _deselectAllPlaylist(self):
        indices = [self.playListCtrl.GetFirstSelected()]
        while indices[-1] != -1:
            indices.append(self.playListCtrl.GetNextSelected(indices[-1]))
        del indices[-1]
        
        for i in range(len(indices)):
            self.playListCtrl.Select(indices[i], on=0)
            
    def _DoSearch(self, text):
        self._deselectAll()
        text = text.lower()
        for i in range(len(self.file_list)):
            current = self.file_list[i][1].lower()
            if current.find(text) != -1:
                self.fileListCtrl.Select(i)
                self.fileListCtrl.Focus(i)
                self.fileListCtrl.SetFocus()
                break
        # return true to tell the search ctrl to remember the text
        return True
    
    def _finishedPlaying(self):
        self.toolbar.EnableTool(ITEM_START, True)
        self.toolbar.EnableTool(ITEM_PAUSE, False)
        self._deselectAllPlaylist()
        wx.CallAfter(self.playListCtrl.Enable, True)
        wx.CallAfter(self.fileListCtrl.Enable, True)
        self._end_trig.stop()
        self._snd_trig.stop()
        self.SetStatusText("Stopped", 0)
        self.gauge.SetValue(0)
    
    def _getFinalPlaylist(self):
        list = []
        for elem in self.play_list:
            if elem[4][0]:
                list.append([elem[1],elem[3][0],elem[5][0],elem[6]])
        return list
    
    def _getWindowPosSize(self, pos, size):
        try:
            f = open(os.path.join(SAVE_PATH, "player_win_infos.pref"), 'r')
        except IOError:
            return [pos, size]
        else:
            temp = f.read()
            pos, size = temp.split(';')
            posx, posy = pos.split(",")
            sizex, sizey = size.split(",")
            ##il semble y avoir un offset de 40 pixels lors de la sauvegarde
            ##de la taille de la fenetre en 'y' alors il est retire ici
            offset = 0
            if wx.Platform == '__WXMAC__':
                offset = 40
            return [(int(posx),int(posy)),(int(sizex),int(sizey)-offset)]
    
    def _ipoutChange(self, evt):
        ip = str(evt.GetEventObject().GetValue())
        self._user_settings['ipout'] = ip
    
    def _linkItems(self, evt):
        msg = "You can only link one analyzed item with one raw item."
        itemCount = self.playListCtrl.GetSelectedItemCount()
        ##si plus de deux items selectionnes, informer l'utilisateur
        if itemCount > 2 or itemCount == 0:
            msg += "\nYou have " + str(self.playListCtrl.GetSelectedItemCount()) + " items selected."
            self._linkErrorDialog(msg)
        else:
            index1 = self.playListCtrl.GetFirstSelected()
            index2 = self.playListCtrl.GetNextSelected(index1)
            ##verifier que les items selectionnes soit un a cote de l'autre
            if (index2-index1) > 1:
                msg += "\nThe items you select have to be next to each other."
                self._linkErrorDialog(msg)
            else:
                ##si les deux items sont du meme type, informer l'utilisateur
                if self.play_list[index1][5][0] == self.play_list[index2][5][0]:
                    type = "Analyzed" if self.play_list[index1][5][0] == 0 else "Raw"
                    msg += "\nYou have selected two " + type + " items."
                    self._linkErrorDialog(msg)
                else:
                    ##si l'item est deja lie, delier
                    if self.play_list[index1][6] != -1:
                        ##changer le texte pour indiquer qu'il n'y a plus de liaison
                        txt1 = self.playListCtrl.GetItemText(index1)
                        txt2 = self.playListCtrl.GetItemText(index2)
                        txt1 = txt1[:-9]
                        txt2 = txt2[:-9]
                        self.playListCtrl.SetItemText(index1, txt1)
                        self.playListCtrl.SetItemText(index2, txt2)
                        self.play_list[index1][6] = -1
                        self.play_list[index2][6] = -1
                    else:
                        ##changer le texte pour indiquer la liaison
                        txt1 = self.playListCtrl.GetItemText(index1)
                        txt2 = self.playListCtrl.GetItemText(index2)
                        txt1 += " (linked)"
                        txt2 += " (linked)"
                        self.playListCtrl.SetItemText(index1, txt1)
                        self.playListCtrl.SetItemText(index2, txt2)
                        
                        ##indiquer le id des liaisons
                        self.play_list[index1][6] = index2
                        self.play_list[index2][6] = index1
            
    def _linkErrorDialog(self, msg):
        dlg = wx.MessageDialog(self, msg,
                               'Link Tool Error',
                               wx.OK | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
    
    def _makeMappingDict(self):
        temp = {}
        for key in self._user_settings:
            if key in ['x','y','z','mag','rgh','act']:
                temp[key] = self._user_settings[key]
        return temp
    
    def _mappingDlg(self, evt):
        dialog = MappingDialog(self, size=(100,100))
        dialog.CenterOnScreen()
        
        dialog.x_ctrl.SetValue(self._user_settings['x'])
        dialog.y_ctrl.SetValue(self._user_settings['y'])
        dialog.z_ctrl.SetValue(self._user_settings['z'])
        dialog.mag_ctrl.SetValue(self._user_settings['mag'])
        dialog.rgh_ctrl.SetValue(self._user_settings['rgh'])
        dialog.act_ctrl.SetValue(self._user_settings['act'])
        
        if dialog.ShowModal() == wx.ID_OK:
            self._user_settings['x'] = str(dialog.x_ctrl.GetValue())
            self._user_settings['y'] = str(dialog.y_ctrl.GetValue())
            self._user_settings['z'] = str(dialog.z_ctrl.GetValue())
            self._user_settings['mag'] = str(dialog.mag_ctrl.GetValue())
            self._user_settings['rgh'] = str(dialog.rgh_ctrl.GetValue())
            self._user_settings['act'] = str(dialog.act_ctrl.GetValue())
        
        dialog.Destroy()
        
    def _markUnsaved(self):
        global PLAYER_STATE
        if PLAYER_STATE['IS_SAVED']:
            PLAYER_STATE['IS_SAVED'] = False
            self._setSessionTitle()
    
    def _menuStart(self, evt):
        if evt.GetEventObject().IsChecked(evt.GetId()):
            self._OnStartTool(evt)
        else:
            self._OnPauseTool(evt)
            
    def _moveItemPlaylistUP(self, evt):
        indices = [self.playListCtrl.GetFirstSelected()]
        
        ##s'assure que le premier element selectionne n'est pas le premier de la liste
        if indices[0] != 0:
            while indices[-1] != -1:
                indices.append(self.playListCtrl.GetNextSelected(indices[-1]))
            del indices[-1]
            
            ##on modifie la playlist
            for index in indices:
                tomove = self.play_list[index-1]
                self.play_list[index-1] = self.play_list[index]
                self.play_list[index] = tomove
            ##on nettoie ultimatelistctrl
            self.playListCtrl.DeleteAllItems()
            ##on retire tous les index de la liste, car ils seront recreer apres
            for i in self.play_list: i[:] = [i[1],i[2],i[3][0],i[4][0],i[5][0],i[6]]
            self._createPlaylistFromFile()
            
            ##montre la nouvelle position des elements dans la liste
            for index in indices:
                self.playListCtrl.Select(index-1)
                self.playListCtrl.Focus(index-1)
            self._markUnsaved()
        
    def _moveItemPlaylistDOWN(self, evt):
        indices = [self.playListCtrl.GetFirstSelected()]
        while indices[-1] != -1:
            indices.append(self.playListCtrl.GetNextSelected(indices[-1]))
        del indices[-1]
        
        ##s'assure que le dernier element selectionne n'est pas le dernier de la liste
        if indices[-1] != self.playListCtrl.GetItemCount()-1:
            ##on doit inverser la liste pour que le traitement se fasse correctement
            indices.reverse()
            
            ##on modifie la playlist
            for index in indices:
                tomove = self.play_list[index+1]
                self.play_list[index+1] = self.play_list[index]
                self.play_list[index] = tomove
            ##on nettoie ultimatelistctrl
            self.playListCtrl.DeleteAllItems()
            ##on retire tous les index de la liste, car ils seront recreer apres
            for i in self.play_list: i[:] = [i[1],i[2],i[3][0],i[4][0],i[5][0],i[6]]
            self._createPlaylistFromFile()
            
            ##montre la nouvelle position des elements dans la liste
            for index in indices:
                self.playListCtrl.Select(index+1)
                self.playListCtrl.Focus(index+1)
            self._markUnsaved()
    
    def _newSessionTitle(self):
        dlg = wx.TextEntryDialog(self, "Enter a name : ", "ACC Data Player - New session", "Untitled", style=wx.OK|wx.CENTRE)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.sessionTitle = dlg.GetValue()
        self._setSessionTitle()
    
    def _OnAddTool(self, evt):
        dlg = wx.FileDialog(
            self, message="Select your file(s)",
            defaultDir=HOME_PATH,
            defaultFile="",
            wildcard=wildcard_accdata,
            style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
            )
            
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            self.gauge.SetRange(len(paths))
            for i, path in enumerate(paths):
                self.gauge.SetValue(i)
                wx.Yield()
                dur = SndTable(path).getDur()
                min = str(int(dur/60))
                secs = "%.1f" % (dur%60)
                self.file_list.append([str(path),str(min+":"+secs)])
                self._addFileInCtrl()
            self.gauge.SetValue(0)
        dlg.Destroy()
        self._markUnsaved()
    
    def _OnNewTool(self, evt):
        global PLAYER_STATE
        PLAYER_STATE['IS_SAVED'] = False
        self.fileListCtrl.DeleteAllItems()
        self.playListCtrl.DeleteAllItems()
        del self.file_list[:]
        del self.play_list[:]
        self._newSessionTitle()
    
    def _OnOpenTool(self, evt):
        dlg = wx.FileDialog(
            self, message="Open a session",
            defaultDir=HOME_PATH,
            defaultFile="",
            wildcard=wildcard_session,
            style=wx.OPEN | wx.CHANGE_DIR
            )
            
        if dlg.ShowModal() == wx.ID_OK:
            file = str(dlg.GetPaths()[0])
            self._openSession(file)
        dlg.Destroy()
    
    def _OnPauseTool(self, evt):
        self._player.stop()
        self._finishedPlaying()
        
    def _OnPlaylistSelect(self, evt):
        indices = [self.playListCtrl.GetFirstSelected()]
        while indices[-1] != -1:
            indices.append(self.playListCtrl.GetNextSelected(indices[-1]))
        del indices[-1]
        
        for item in indices:
            if self.play_list[item][6] != -1:
                self.playListCtrl.Select(self.play_list[item][6], on=1)
    
    def _onQuit(self, evt):
        if PLAYER_STATE['IS_SAVED']:
            self._saveWindowPosSize()
            self.Destroy()
        else:
            dialog = wx.MessageDialog(self, 'The session currently opened is not saved.\nAll changes will be lost if the application closes.',
                                   'Warning!',
                                   wx.OK | wx.ICON_INFORMATION | wx.CANCEL)
            if dialog.ShowModal() == wx.ID_OK:
                self._saveWindowPosSize()
                self.Destroy()
        
    def _OnSaveTool(self, evt):
        dlg = wx.FileDialog(
            self, message="Save session as ...", defaultDir=HOME_PATH, 
            defaultFile=".acc", wildcard=wildcard_session, style=wx.SAVE
            )
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._saveSession(path)
        dlg.Destroy()
        
    def _OnStartTool(self, evt):
        self.playListCtrl.Disable()
        self.fileListCtrl.Disable()
        
        self.toolbar.EnableTool(ITEM_START, False)
        self.toolbar.EnableTool(ITEM_PAUSE, True)
        
        ##verifier pour un offset
        if self.playListCtrl.GetSelectedItemCount() > 0:
            offset = self.playListCtrl.GetFirstSelected()
            
            while self.play_list[offset][4][0] == False:
                offset += 1
        else:
            offset = 0
        
        if PLAYER_STATE['IS_READY']:
            self._player.setOSC(self._user_settings['portout'],self._user_settings['ipout'],self._makeMappingDict())
            self._player.setPlaylist(self._getFinalPlaylist())
            self._player.play(offset=offset)
            self._end_trig.play()
            self._snd_trig.play()
        else:
            self._createPlayer(offset=offset)
        
        ##selection de l'item en lecture
        self.playListCtrl.Select(offset)
        
        self.SetStatusText("Playing", 0)
        self.gauge.SetRange(len(self._getFinalPlaylist()))
        self.gauge.SetValue(self._player.getCount())
        wx.Yield()
        
    def _openSession(self, file):
        self.gauge.Pulse()
        wx.Yield()
        
        global PLAYER_STATE
        PLAYER_STATE['IS_SAVED'] = True
        
        self.fileListCtrl.DeleteAllItems()
        self.playListCtrl.DeleteAllItems()
        f = open(file, 'r')
        content = f.readlines()
        for i in range(len(content)):content[i]=content[i].replace("\n","")
        ##title
        self.sessionTitle = content[0].replace("\n","")
        self._setSessionTitle()
        ##library
        del self.file_list[:]
        temp = content[1].split(";")
        for i in range(len(temp)):
            self.gauge.Pulse()
            wx.Yield()
            self.file_list.append(temp[i].split(","))
            self._addFileInCtrl()
        ##playlist
        del self.play_list[:]
        temp = content[2].split(";")
        for i in range(len(temp)):
            self.gauge.Pulse()
            wx.Yield()
            self.play_list.append(temp[i].split(","))
            self.play_list[i][2] = int(self.play_list[i][2])
            self.play_list[i][4] = int(self.play_list[i][4])
            self.play_list[i][5] = int(self.play_list[i][5])
            if self.play_list[i][3] == "True":
                self.play_list[i][3] = True
            else:
                self.play_list[i][3] = False
        self._createPlaylistFromFile()
        ##osc
        temp = content[3].split(";")
        for i in range(len(temp)):
            self.gauge.Pulse()
            wx.Yield()
            current = temp[i].split(":")
            self._user_settings[current[0]] = current[1]
        self.portout_ctrl.SetValue(str(self._user_settings['portout']))
        self.ipout_ctrl.SetValue(self._user_settings['ipout'])
        self.gauge.SetValue(0)
    
    def _portoutChange(self, evt):
        port = str(evt.GetEventObject().GetValue())
        if port != '':
            self._user_settings['portout'] = int(port)
    
    def _rearrangeIndexes(self, list):
        """
        list 0 == File list
        list 1 == Play list
        """
        if list==0:
            for i in range(len(self.file_list)):
                self.file_list[i][0] = i
        elif list==1:
            for i in range(len(self.play_list)):
                self.play_list[i][0] = i
    
    def _removeItemFileList(self, evt):
        indices = [self.fileListCtrl.GetFirstSelected()]
        while indices[-1] != -1:
            indices.append(self.fileListCtrl.GetNextSelected(indices[-1]))
        del indices[-1]
        
        for i in range(len(indices)):
            current = indices[i]
            for j in range(len(self.file_list)):
                if self.file_list[j][0] == current:
                    del self.file_list[j]
                    break
            ##current-i compense le fait que la liste qui reduit
            self.fileListCtrl.DeleteItem(current-i)
        self._rearrangeIndexes(0)
        self._markUnsaved()
        
    def _removeItemPlaylist(self, evt):
        indices = [self.playListCtrl.GetFirstSelected()]
        while indices[-1] != -1:
            indices.append(self.playListCtrl.GetNextSelected(indices[-1]))
        del indices[-1]
        
        for i in range(len(indices)):
            current = indices[i]
            for j in range(len(self.play_list)):
                if self.play_list[j][0] == current:
                    del self.play_list[j]
                    break
            ##current-i compense le fait que la liste qui reduit
            self.playListCtrl.DeleteItem(current-i)
        self._rearrangeIndexes(1)
        self._markUnsaved()
    
    def _saveSession(self, path):
        try:
            dot = path.rindex(".")
            ext = path[dot:]
            if ext != ".acc":
                path = path[:dot]+".acc"
        except:
            path += ".acc"
        
        f = open(path, 'w')
        ##title
        f.write(self.sessionTitle+"\n")
        ##library
        size = len(self.file_list)
        for i in range(size):
            f.write(str(self.file_list[i][1])+","+str(self.file_list[i][2]))
            if i < size-1:
                f.write(";")
        f.write("\n")
        ##playlist
        size = len(self.play_list)
        for i in range(size):
            f.write(str(self.play_list[i][1])+","+str(self.play_list[i][2])+","+
                    str(self.play_list[i][3][0])+","+str(self.play_list[i][4][0])
                    +","+str(self.play_list[i][5][0])+","+str(self.play_list[i][6]))
            if i < size-1:
                f.write(";")
        f.write("\n")
        ##osc
        size = len(self._user_settings)
        for i, key in enumerate(self._user_settings):
            if key == 'portout':
                f.write(key+":"+str(self._user_settings[key]))
            else:
                f.write(key+":"+self._user_settings[key])
            if i < size-1:
                f.write(";")
        f.write("\n")
        f.close()
        
        global PLAYER_STATE
        PLAYER_STATE['IS_SAVED'] = True
        self._setSessionTitle()
    
    def _saveWindowPosSize(self):
        pos = self.GetPosition()
        size = self.GetSize()
        try:
            f = open(os.path.join(SAVE_PATH, "player_win_infos.pref"), 'w')
            f.write(str(pos[0])+","+str(pos[1]))
            f.write(";")
            f.write(str(size[0])+","+str(size[1]))
        except IOError:
            pass
        else:
            f.close()
    
    def _setItemType(self, evt):
        id = evt.GetId()
        obj = evt.GetEventObject()
        for i in range(len(self.play_list)):
            if self.play_list[i][5][1] == id:
                self.play_list[i][5][0] = obj.GetCurrentSelection()
                break
        self._markUnsaved()
    
    def _setSessionTitle(self):
        if PLAYER_STATE['IS_SAVED']:
            self.SetStatusText("Session name : "+self.sessionTitle, 1)
            self.SetTitle(self.windowTitle+" - "+self.sessionTitle)
        else:
            self.SetStatusText("Session name : *"+self.sessionTitle, 1)
            self.SetTitle(self.windowTitle+" - *"+self.sessionTitle)
    
    def _updateTrackPlaying(self):
        index = self.playListCtrl.GetFirstSelected()
        
        if self.play_list[index][6] != -1:
            index += 2
        else:
            index += 1
        
        while self.play_list[index][4][0] == False:
            index += 1
        self._deselectAllPlaylist()
        ##si l'item a lire est lie, selectionner son compagnon
        if self.play_list[index][6] != -1:
            self.playListCtrl.Select(self.play_list[index][6])
        self.playListCtrl.Select(index)
        self.gauge.SetValue(self._player.getCount())
        wx.Yield()

class MappingDialog(wx.Dialog):
    def __init__(self, parent, size, pos=wx.DefaultPosition):
        
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, title="Mapping outgoing streams", pos=pos, size=size)
        self.PostCreate(pre)
        
        if wx.Platform == '__WXMAC__':
            self.SetExtraStyle(wx.DIALOG_EX_METAL)
            
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        ##X addr
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Raw X address:")
        label.SetHelpText("Address for the x-axis stream.")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.x_ctrl = wx.TextCtrl(self, -1)
        box.Add(self.x_ctrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        
        ##Y addr
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Raw Y address:")
        label.SetHelpText("Address for the y-axis stream.")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.y_ctrl = wx.TextCtrl(self, -1)
        box.Add(self.y_ctrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL)

        ##Z addr
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Raw Z address:")
        label.SetHelpText("Address for the z-axis stream.")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.z_ctrl = wx.TextCtrl(self, -1)
        box.Add(self.z_ctrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        
        ##MAG addr
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Magnitude address:")
        label.SetHelpText("Address for the magnitude stream.")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.mag_ctrl = wx.TextCtrl(self, -1)
        box.Add(self.mag_ctrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        
        ##RGH addr
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Roughness address:")
        label.SetHelpText("Address for the roughness stream.")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.rgh_ctrl = wx.TextCtrl(self, -1)
        box.Add(self.rgh_ctrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        
        ##ACT addr
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Activity address:")
        label.SetHelpText("Address for the activity stream.")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.act_ctrl = wx.TextCtrl(self, -1)
        box.Add(self.act_ctrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
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

if __name__ == '__main__':
    s = Server().boot().start()
    app = wx.App(False)
    #wx.ArtProvider.Push(PlayerArtProvider())
    frame = PlayerFrame(None, size=(1000,600), pos=(100,100))
    frame.Show()
    app.MainLoop()