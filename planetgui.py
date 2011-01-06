#!/usr/bin/env python

# 2005-08-29

import os, time, webbrowser
import rssplanet
from wxPython.wx import *

######### DEFAULTS ARE SET IN rssplanet.py

interval = rssplanet.delay
feeds    = rssplanet.feeds
restartplanet = True
last_update   = time.time() - interval + 60
last_update_graphics = 0		# for tracking inline rendering
gui_interval  = 150
rssplanet.items = []

for x in ('ID_ABOUT', 'ID_EXIT', 'ID_DATE', 'ID_TIMER',
   'ID_APPLY', 'ID_MAIN', 'ID_TEXT', 'ID_OPEN', 'ID_MODE', 'ID_UPDATE', 'ID_MARKER'):
	globals()[x] = wxNewId()

class MainWindow(wxFrame):
    def __init__(s, parent,id, title):
        wxFrame.__init__(s, parent, wxID_ANY, title, size = (400, 350),
                                        style = wxDEFAULT_FRAME_STYLE|
                                        wxNO_FULL_REPAINT_ON_RESIZE)
        s.CreateStatusBar()

        filemenu = wxMenu()
        filemenu.Append(ID_ABOUT, "&About"," Information about this program")
        filemenu.AppendSeparator()
        filemenu.Append(ID_EXIT, "E&xit"," Quit the program")

        menuBar = wxMenuBar()
        menuBar.Append(filemenu,"&File")
        s.SetMenuBar(menuBar)
        EVT_MENU(s, ID_ABOUT, s.OnAbout)
        EVT_MENU(s, ID_EXIT, s.OnExit)
	
        s.mainPanel = wxPanel(size = wxSize(400, 334), parent = s, id = ID_MAIN,
		name = 'panel1', style = wxTAB_TRAVERSAL | wxCLIP_CHILDREN, pos = wxPoint(0, 0))
        s.mainPanel.SetAutoLayout(True)

	wxStaticText(s.mainPanel, -1, "Mode:", pos = wxPoint(10, 32))
	s.modemenu = wxChoice(parent = s.mainPanel, pos = wxPoint(80, 30), size = wxSize(150, 30),
		choices = ["xplanet", "OSXplanet"], style = 0, id = ID_MODE)
	if rssplanet.start_xplanet: s.modemenu.SetSelection(0)
	else: s.modemenu.SetSelection(1)
	EVT_CHOICE(s, ID_MODE, s.change_mode)

	wxStaticText(s.mainPanel, -1, "Update every:", pos = wxPoint(10, 62))
	s.updatemenu = wxChoice(parent = s.mainPanel, pos = wxPoint(100, 60), size = wxSize(130, 30),
	  choices = ["5 minutes", "10 minutes", "20 minutes", "30 minutes"], style = 0, id = ID_UPDATE)
	s.updatemenu.SetSelection(min(int(rssplanet.delay / 600.), 3))
	EVT_CHOICE(s, ID_UPDATE, s.change_update)

	wxStaticText(s.mainPanel, -1, "Marker style:", pos = wxPoint(10, 92))
	s.markermenu = wxChoice(parent = s.mainPanel, pos = wxPoint(100, 90), size = wxSize(130, 30),
	  choices = ["Circles", "Icons"], style = 0, id = ID_MARKER)
	if rssplanet.icons: s.markermenu.SetSelection(1)
	else: s.markermenu.SetSelection(0)
	EVT_CHOICE(s, ID_MARKER, s.change_marker)

        s.applyButton = wxButton(label = 'Update Now', id = ID_APPLY,
		parent = s.mainPanel, name = 'applyButton', size = wxSize(100, 25),
			style = 0, pos = wxPoint(250, 270))
        EVT_BUTTON(s.applyButton, ID_APPLY, s.bapply)

        s.openButton = wxButton(label = 'Open', id = ID_OPEN,
		parent = s.mainPanel, name = 'openButton', size = wxSize(100, 25),
			style = 0, pos = wxPoint(50, 270))
        EVT_BUTTON(s.openButton, ID_OPEN, s.bopen)

	s.boxes = []
	for x, n in zip(feeds, range(len(feeds))):
       		s.boxes.append(wxCheckBox(label = x[1], id = wxNewId(), parent = s.mainPanel,
			name = 'feedCheckBox', size = wxSize(150, 25), style = 0,
				pos = wxPoint(250, 10 + n * 30)))
		s.boxes[-1].SetValue(x[2])
	s.scroll = wxTextCtrl(size = wxSize(380, 30), parent = s, id = ID_TEXT,
		name = 'text', style = wxTE_READONLY, pos = wxPoint(10, 220))
	s.scrolltext = 30 * ' '
	s.last_up = wxStaticText(s.mainPanel, -1, '', pos = wxPoint(110, 310))
	s.items = []
	s.cur_item = 0

        s.Show(1)

    def status(s, x):
    	try: s.mkstatus()
	except: return

    def secs_to_text(s, x):
    	m, s = divmod(x, 60.)
	m, s = int(m), int(s)
	mt, st = "minute", "second"
	if m != 1: mt += 's'
	if s != 1: st += 's'
	if m: return "%i %s, %i %s" % (m, mt, s, st)
	else: return "%i %s" % (s, st)

    def mkstatus(s):
	secs = interval - time.time() + last_update
	s.SetStatusText("%s until next update" % s.secs_to_text(secs))
	if secs < 0:
		s.update()
	if rssplanet.web_render and (time.time() -
			last_update_graphics) > rssplanet.draw_delay:
		rssplanet.inline_render()
		last_update_graphics = time.time()

	if not s.items: return
	s.scrolltext = s.scrolltext[1:]
	if len(s.scrolltext) < 75:
		s.cur_item += 1
		if s.cur_item >= len(s.items):
			s.cur_item = 0
		s.scrolltext += '  ***  ' + s.items[s.cur_item][1]
	s.scroll.SetValue(s.scrolltext)

    def change_mode(s, x = None):
    	c = s.modemenu.GetSelection()
	if not c: rssplanet.start_xplanet = True
	else: rssplanet.start_xplanet = False
	rssplanet.launch_xplanet()

    def change_marker(s, x = None):
    	c = s.markermenu.GetSelection()
	if c: rssplanet.icons = True
	else: rssplanet.icons = False
	timer.Stop()
	rssplanet.write_marker_file()
	timer.Start(gui_interval)

    def change_update(s, x = None):
    	global interval

    	c = int(s.updatemenu.GetStringSelection().split()[0])
	interval  = c * 60

    def bapply(s, x = None):
    	global restartplanet

	for x, n in zip(feeds, range(len(feeds))):
		if s.boxes[n].IsChecked():
			x[2] = True
		else:
			x[2] = False
	rssplanet.feeds = feeds
	if restartplanet:
		rssplanet.launch_xplanet()
		restartplanet = False
	s.run_rssplanet()

    def bopen(s, x = None):
    	try: url = s.items[s.cur_item][2]
	except: url = ''
	if not url: return
	rssplanet.printout(url)
	webbrowser.open_new(url)

    def update(s):
    	s.bapply()

    def run_rssplanet(s):
    	global last_update, timer

	timer.Stop()
    	s.SetStatusText("Fetching news...")
	s.Refresh()
	s.Update()
	rssplanet.items = []
	rssplanet.dropcount = {}
	rssplanet.update()
	rssplanet.write_marker_file()
    	s.SetStatusText('')
	last_update = time.time()
	if rssplanet.items:
		s.items = rssplanet.items
		s.cur_item = 10000
	s.last_up.SetLabel("Last updated " + time.strftime("%Y-%m-%d %H:%M",
				time.localtime(last_update)))
	timer.Start(gui_interval)
 
    def OnAbout(s,e):
        d = wxMessageDialog(s,
		" A newsmapper for \n"
		" xplanet/OSXplanet \n\n"
		" by Martin C. Doege \n",
		"About RSS-Planet", wxOK)
        d.ShowModal()
        d.Destroy()

    def OnExit(s,e):
        s.Close(True)

app = wxPySimpleApp()
frame = MainWindow(None, -1, "RSS-Planet %s" % rssplanet.__version__)

timer = wxTimer(app, ID_TIMER)
EVT_TIMER(app, ID_TIMER, frame.status)
timer.Start(gui_interval)
app.MainLoop()
