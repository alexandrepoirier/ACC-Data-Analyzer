import wx
import os
import sys
from time import sleep, strftime

class TabbedFrame(wx.Frame):
    
    """
    A wx.Frame subclass which uses a toolbar to implement tabbed views and
    invokes the native 'selected' look on OS X when running wxPython version
    2.8.8.0 or higher.
    
    To use:
    - Create an instance.
    - Call CreateTabs with a list of (label, bitmap) pairs for the tabs.
    - Override OnTabChange(tabIndex) to respond to the user switching tabs.
    
    The native selection look on OS X requires that only one toolbar item be
    active at a time (like radio buttons). There is no such requirement with
    the toggle tools in wx, which is why the native look is not used (see
    http://trac.wxwidgets.org/ticket/8789). But this class enforces that
    exactly one tool is toggled at a time, so the native look can be enabled
    by loading the Carbon and CoreFoundation frameworks via ctypes and
    manipulating the toolbar.
    """

    def CreateTabs(self, tabs):
        """
        Create the toolbar and add a tool for each tab.
        
        tabs -- List of (label, bitmap) pairs.
        """
        
        # Create the toolbar
        self.tabIndex = 0
        self.toolbar = self.CreateToolBar(style=wx.TB_HORIZONTAL|wx.TB_TEXT)
        for i, tab in enumerate(tabs):
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
            self.toolbar.ToggleTool(0, True)
            self.Bind(wx.EVT_TOOL, self.OnToolBarDefault)
            
        self.Show()
    
    def OnTabChange(self, tabIndex):
        """Respond to the user switching tabs."""
        
        pass

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
        # Get references to the toolbar items (note: separators count)
        self.macToolbarItems = [core.CFArrayGetValueAtIndex(p, i)
                                for i in xrange(self.toolbar.GetToolsCount())]
        # Set the native "selected" state on the first tab
        # 128 corresponds to kHIToolbarItemSelected (1 << 7)
        item = self.macToolbarItems[self.tabIndex]
        self.carbon.HIToolbarItemChangeAttributes(item, 128, 0)

    def OnToolBarDefault(self, event):
        """Ensure that there is always one tab selected."""

        i = event.GetId()
        if i in xrange(self.toolbar.GetToolsCount()):
            self.toolbar.ToggleTool(i, True)
            if i != self.tabIndex:
                self.toolbar.ToggleTool(self.tabIndex, False)
                self.OnTabChange(i)
                self.tabIndex = i
        else:
            event.Skip()
    
    def OnToolBarMacNative(self, event):
        """Manage the toggled state of the tabs manually."""
        
        i = event.GetId()
        if i in xrange(self.toolbar.GetToolsCount()):
            self.toolbar.ToggleTool(i, False)  # Suppress default selection
            if i != self.tabIndex:
                # Set the native selection look via the Carbon APIs
                # 128 corresponds to kHIToolbarItemSelected (1 << 7)
                item = self.macToolbarItems[i]
                self.carbon.HIToolbarItemChangeAttributes(item, 128, 0)
                self.OnTabChange(i)
                self.tabIndex = i
        else:
            event.Skip()

class PanelSettings(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos=pos, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        self.SetBackgroundColour("#222222")
        
        self.osc_block = (10,10)
        self.addresses_block = (10,135)
        self.mapping_block = (275,10)
        self.analyse_block = (275,135)
        self._user_settings = {}
        self._default_settings = {'portin':"8000",'portout':"10000",'ipout':"127.0.0.1",
                                  'stream_type':0,'map_mag':"/mag",'map_rgh':"/rgh",'map_act':"/act",
                                  'smoothing':True,'thresh':20}
        
        ##OSC block
        self.pos_portin = (self.osc_block[0], self.osc_block[1]+30)
        self.portin = wx.TextCtrl(self, value="8000", pos=(self.pos_portin[0]+90, self.pos_portin[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        self.pos_portout = (self.osc_block[0], self.osc_block[1]+60)
        self.portout = wx.TextCtrl(self, value="10000", pos=(self.pos_portout[0]+90, self.pos_portout[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        self.pos_ipout = (self.osc_block[0], self.osc_block[1]+90)
        self.ipout = wx.TextCtrl(self, value="127.0.0.1", pos=(self.pos_ipout[0]+90, self.pos_ipout[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        ##ADDRESSES block
        self.pos_choice = (self.addresses_block[0], self.addresses_block[1]+32)
        self.choice = wx.Choice(self, pos=(self.pos_choice[0]+100, self.pos_choice[1]-2), choices=["List","Seperate"])
        
        self.pos_addr1 = (self.addresses_block[0], self.addresses_block[1]+60)
        self.addr1 = wx.TextCtrl(self, value="", pos=(self.pos_addr1[0]+90, self.pos_addr1[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        self.pos_addr2 = (self.addresses_block[0], self.addresses_block[1]+90)
        self.addr2 = wx.TextCtrl(self, value="", pos=(self.pos_addr2[0]+90, self.pos_addr2[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        self.pos_addr3 = (self.addresses_block[0], self.addresses_block[1]+120)
        self.addr3 = wx.TextCtrl(self, value="", pos=(self.pos_addr3[0]+90, self.pos_addr3[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        self._setStreamType(wx.EVT_CHOICE)
        
        ##ANALYSIS block
        self.pos_check = (self.analyse_block[0]-2,self.analyse_block[1]+32)
        self.check = wx.CheckBox(self, pos=self.pos_check, style=wx.CHK_2STATE)
        self.check.SetValue(True)
        self.pos_slider = (self.analyse_block[0]+15,self.analyse_block[1]+80)
        self.thresh_slider = wx.Slider(self, value=20, minValue=1, maxValue=50, pos=self.pos_slider)
        
        ##MAPPING block
        self.pos_mag = (self.mapping_block[0], self.mapping_block[1]+30)
        self.mag = wx.TextCtrl(self, value="/mag", pos=(self.pos_mag[0]+90, self.pos_mag[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        self.pos_rgh = (self.mapping_block[0], self.mapping_block[1]+60)
        self.rgh = wx.TextCtrl(self, value="/rgh", pos=(self.pos_rgh[0]+90, self.pos_rgh[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        self.pos_act = (self.mapping_block[0], self.mapping_block[1]+90)
        self.act = wx.TextCtrl(self, value="/act", pos=(self.pos_act[0]+90, self.pos_act[1]), 
                                  size=(100,20), style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
                                  
        self.pos_btn_accept = (275,250)
        self.btn_accept = wx.Button(self, wx.ID_APPLY, "Apply changes", pos=self.pos_btn_accept)
        self.pos_btn_reset = (400,250)
        self.btn_reset = wx.Button(self, wx.ID_CLEAR, "Reset", pos=self.pos_btn_reset)
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SCROLL, self._sliderEvt)
        self.Bind(wx.EVT_CHECKBOX, self._checked)
        self.Bind(wx.EVT_CHOICE, self._setStreamType)
        self.Bind(wx.EVT_BUTTON, self._apply, id=wx.ID_APPLY)
        self.Bind(wx.EVT_BUTTON, self._reset, id=wx.ID_CLEAR)
        
        self._importUserSettings()
        
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen("#666666", 2))
        dc.SetTextForeground("#AAAAAA")
        
        ##Font titres
        font = wx.Font(14, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
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
        font = wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
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
        
    def _apply(self, evt):
        self._user_settings['portin'] = self.portin.GetValue()
        self._user_settings['portout'] = self.portout.GetValue()
        self._user_settings['ipout'] = self.ipout.GetValue()
        self._user_settings['stream_type']= self.choice.GetCurrentSelection()
        self._user_settings['map_mag'] = self.mag.GetValue()
        self._user_settings['map_rgh'] = self.rgh.GetValue()
        self._user_settings['map_act'] = self.act.GetValue()
        self._user_settings['smoothing'] = self.check.GetValue()
        self._user_settings['thresh'] = self.thresh_slider.GetValue()
        self._saveParamToFile()

    def _checked(self, evt):
        if self.check.GetValue():
            print "Smoothing is on baby."
        else:
            print "Never turn that off again..."
            
    def _importUserSettings(self):
        try:
            f = open(os.getcwd()+"/preferences.txt", 'r')
            for line in f:
                key, value = line.rsplit(':')
                value = value.replace('\n', '')
                if key == 'stream_type' or key == 'thresh':
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
        f = open(os.getcwd()+"/preferences.txt", 'w')
        for key in self._user_settings:
            f.write(key+':'+str(self._user_settings[key])+'\n')
        f.close()
        print 'Saved preferences to disk.'
        
    def _sliderEvt(self, evt):
        self.Refresh()

    def _setStreamType(self, evt):
        type = self.choice.GetCurrentSelection()
        if type == 0:
            """Type list"""
            self.addr1.SetValue("/accxyz")
            self.addr2.Enable(False)
            self.addr2.SetBackgroundColour("#555555")
            self.addr2.SetValue("")
            self.addr3.Enable(False)
            self.addr3.SetBackgroundColour("#555555")
            self.addr3.SetValue("")
        elif type == 1:
            """Type seperate"""
            self.addr1.SetValue("/x")
            self.addr2.Enable()
            self.addr2.SetBackgroundColour("#FFFFFF")
            self.addr2.SetValue("/y")
            self.addr3.Enable()
            self.addr3.SetBackgroundColour("#FFFFFF")
            self.addr3.SetValue("/z")

class RedirectText():
    def __init__(self, textCtrl):
        self.out = textCtrl

    def write(self, string):
        wx.CallAfter(self.out.WriteText, string)

class PanelViewData(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos=pos, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour("#222222")
        
        log = wx.TextCtrl(self, wx.ID_ANY, size=(size[0]-10,size[1]-22), pos=(10,0),
                          style = wx.TE_MULTILINE|wx.TE_READONLY|wx.NO_BORDER|wx.TE_BESTWRAP)
        log.SetBackgroundColour("#222222")
        log.SetForegroundColour("#AAAAAA")
        font = wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        log.SetFont(font)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(log, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)
        
        redir = RedirectText(log)
        sys.stdout = redir
        sys.stderr = redir
        
        self._initializeSession()
        
    def _initializeSession(self):
        print '\nSession started on : '
        print strftime('%d %b %Y %Hh%M')
        print '-------------------------------'
        
class PanelControls(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos=pos, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour("#222222")

        self.btn_size = (100,50)
        self.pos_btn = (125,100)
        self.start_btn = wx.Button(self, wx.ID_FORWARD, "START\n", pos=(self.pos_btn[0],self.pos_btn[1]), size=self.btn_size)
        self.stop_btn = wx.Button(self, wx.ID_STOP, "STOP\n", pos=(self.pos_btn[0]+120,self.pos_btn[1]), size=self.btn_size)
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_BUTTON, self._start, id=wx.ID_FORWARD)
        self.Bind(wx.EVT_BUTTON, self._stop, id=wx.ID_STOP)
        
    def OnPaint(self, evt):
        pass
        
    def _start(self, evt):
        print "start!"
        
    def _stop(self, evt):
        print "stopped"

if __name__ == '__main__':
    app = wx.App(False)
    size = (32, 32)
    tabs = [
        ('Settings', wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, size=size)),
        ('View Data', wx.ArtProvider.GetBitmap(wx.ART_REPORT_VIEW, size=size)),
        ('Controls', wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, size=size))
    ]
    fstyle = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX)
    size = (500,308)
    frame = TabbedFrame(None, pos=(100,100), size=size, style=fstyle)
    frame.CreateTabs(tabs)
    
    #TABS
    view_data = PanelViewData(frame, (0,0), size)
    settings = PanelSettings(frame, (0,0), size)
    controls = PanelControls(frame, (0,0), size)
    
    #INIT
    settings.Show()
    view_data.Show(False)
    controls.Show(False)
    
    def OnTabChange(tabIndex):
        if tabIndex == 0:
            settings.Show()
            view_data.Show(False)
            controls.Show(False)
        if tabIndex == 1:
            settings.Show(False)
            view_data.Show()
            controls.Show(False)
        if tabIndex == 2:
            settings.Show(False)
            view_data.Show(False)
            controls.Show()
        
    frame.OnTabChange = OnTabChange
    frame.Show()
    app.MainLoop()