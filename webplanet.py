#!/usr/bin/env python

# 2008-11-17

import os.path, shutil
try: import Image
except: pass

p_top  = 10	# top left position
p_left = 10	#   of image on page
home_url = 'http://home.arcor.de/mdoege/rss-planet/'	# URL of homepage

def ll2xy(lon, lat):
	lon, lat = float(lon), float(lat)
	posx = (180. + lon) / 360. * w + p_left
	posy = (90.  - lat) / 180. * h + p_top
	return posx, posy

def output_html(f, items, res, ic, web_path = 'web', mfile = 'rssitems'):
	"Output the news items as HTML to file f."
	global w, h, wi, hi

	w, h = res[0], res[1]
	wi, hi = ic[0], ic[1]

	p0 = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\
			"http://www.w3.org/TR/html4/loose.dtd">\n'
	p1 = '<html><head><title>RSS-Planet Newsmap</title><meta http-equiv="refresh" content="1200"></head><body text="#ffff00">\n'
	p2 = '<div style="position:absolute; top:%upx; left:%upx;">\n' % (p_top, p_left)
	p3 = '<img src="rssplanet.png.jpg" width="%s" height="%s" alt="RSS-Planet background"></div>\n' % (w, h)
	p5 = '<div style="position:absolute; top:%upx; left:%upx;"><a href="%s">Return to home page</a></div>\n' % (
							h + 20 + p_top, p_left, home_url)
	p6 = '<script language="JavaScript" type="text/javascript" src="wz_tooltip.js"></script></body></html>\n'
	p4 = ''
	for c, t, u in items:
		lat, lon = c
		posx, posy = ll2xy(lon, lat)
		p4 += ('<div style="position:absolute; cursor:hand; \
				top:%ipx; left:%ipx; width:%upx; height:%upx" \
				onclick="window.location = \'%s\'" \
				onmouseover="return escape(\'%s\')">&bull;</div>\n'
				% (posy - int(hi / 2), posx - int(wi / 4), wi, hi,
				u.replace('&', '&amp;').replace('=', '&#61;'),
				t.replace("'", "\\'").replace('"', "\\'")))
	f.write( p0 + p1 + p2 + p3 + process_rssitems(mfile, web_path) + p4 + p5 + p6 )

def process_rssitems(fn, web_path):
	global icons

	f = open(fn, 'r')
	out = ''
	icons = []
	for x in f.readlines():
		try:
			pos, text, o = x.strip().split('"')
			e = pos.split()
			lat = e[0]
			lon = e[1]
			other = {}
			for y in o.split():
				za, zb = y.split('=')
				other[za] = zb
			im = other.get('image')
			if im and im.lower() != 'none':
				text = '<img src="%s" alt="logo">' % im.split('/')[-1] + text
				if im not in icons:
					icons.append(im)
			posx, posy = ll2xy(lon, lat)
			out += ('<div style="position:absolute; \
				top:%ipx; left:%ipx; color:%s"> \
				%s</div>\n'
				% (posy - hi, posx - int(wi / 2), other.get('color', '').replace('0x', '#'),
					text))
		except: pass
	try: copy_icons(web_path)
	except: print "Copying of icons to web directory failed."
	return out

def copy_icons(web_path):
	for x in icons:
		bname = x.split('/')[-1]
		wname = os.path.join(web_path, bname)

		try:
			g = Image.open(wname)
		except: pass
		else: continue

		try:
			f = Image.open(x)
			f2 = f.convert("RGBA")
			d = f2.getdata()
			rr, rg, rb, ra = d[0]
			if ra:
				o = []
				for y in d:
					if y[0] == rr and y[1] == rg and y[2] == rb:
						o.append((0, 0, 0, 0))
					else:
						o.append(y)
				f2.putdata(o)
				f2.save(wname)
			else:
				raise Exception
		except:
			shutil.copyfile(x, wname)

