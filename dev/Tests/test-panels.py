import wx
        
class PanelOne(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos=pos, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self._isShown = True
        
        ## TEST
        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, -1, "This is a wx.Dialog")
        label.SetHelpText("This is the help text for the label")
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, "Field #1:")
        label.SetHelpText("This is the help text for the label")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        #text = wx.TextCtrl(self, -1, "", size=(80,-1))
        #text.SetHelpText("Here's some help text for field #1")
        #box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, "Field #2:")
        label.SetHelpText("This is the help text for the label")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        text = wx.TextCtrl(self, -1, "", size=(80,-1))
        text.SetHelpText("Here's some help text for field #2")
        box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            btnsizer.AddButton(btn)
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("The OK button completes the dialog")
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("The Cancel button cancels the dialog. (Cool, huh?)")
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)


        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        if self._isShown:
            dc.SetPen(wx.Pen("#AAAAAA"))
            dc.SetTextForeground("#AAAAAA")
            #font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, face="Eurostile")
            #dc.SetFont(font)
            dc.DrawText("Fenetre 1", 200, 20)
        else:
            dc.Clear()
            
    def hide(self):
        self.Hide()
        self._isShown = False

class PanelTwo(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos=pos, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        
if __name__ == "__main__":
    class MyFrame(wx.Frame):
        def __init__(self, parent=None, id=wx.ID_ANY, title="Test de fenetres multiples", pos=(100,100), size=(500,300)):
            wx.Frame.__init__(self, parent, id, title, pos, size)
            self.panel = PanelOne(self, (0,25), (size[0],size[1]-25))
            self.panel.SetBackgroundColour("#222222")
            
            self.panel2 = PanelOne(self, (0,25), (size[0],size[1]-25))
            self.panel2.SetBackgroundColour("#4444AA")
            self.panel2.Show(False)
            
            button = wx.Button(self, 1004, "Change panels")
            button.SetPosition((100, 15))
            self.Bind(wx.EVT_BUTTON, self.ChangePanel, button)

            self.Show()


        def OnCloseMe(self, event):
            self.Close(True)

        def OnCloseWindow(self, event):
            self.Destroy()
            
        def ChangePanel(self, event):
            self.panel2.Show()
            self.panel.hide()

    app = wx.App(False)
    frame = MyFrame()
    app.MainLoop()