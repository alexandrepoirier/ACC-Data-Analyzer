#!/usr/bin/env python
# encoding: utf-8
import wx
from pyo import *
from pyolib._wxwidgets import SndViewTablePanel, HRangeSlider, BACKGROUND_COLOUR

s = Server().boot()
t = SndTable('/Users/alex/Desktop/verre.wav')
dur = t.getDur(False)

class MyFrame(wx.Frame):
    def __init__(self, parent, title, pos, size):
        wx.Frame.__init__(self, parent, -1, title, pos, size)
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(BACKGROUND_COLOUR)
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.view = SndViewTablePanel(self.panel, t)
        self.box.Add(self.view, 1, wx.EXPAND|wx.ALL, 5)
        self.zoomH = HRangeSlider(self.panel, minvalue=0, maxvalue=1, init=None, pos=(0,0), size=(200,15), 
                 valtype='float', log=False, function=self.setZoomH)
        self.box.Add(self.zoomH, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        self.panel.SetSizer(self.box)
        self.Show()

    def setZoomH(self, values):
        self.view.setBegin(dur * values[0])
        self.view.setEnd(dur * values[1])
        wx.CallAfter(self.view.setImage)

if __name__ == "__main__":
    app = wx.App(False)
    mainFrame = MyFrame(None, title='Waveform viewer', pos=(100,100), size=(500,300))
    app.MainLoop()
