#!/usr/bin/env python

# Draw the day/night distribution in rectangular projection.
# 2007-07-17

# Based on Sun position Python code
# by Grzegorz Rakoczy
# which in turn is based on the web page
#  http://www.stjarnhimlen.se/comp/tutorial.html
# by Paul Schlyter

from math import *
import os, sys, time
import Image

day   = "earth"		# images for day
night = "night"		#   and night

blur = 4.		# blur angle for terminator

phong    = True		# enable Phong shading
shad_div = 260.		# * shading intensity dividend
			#    (higher value -> brighter shading)
diff_int = 1.		# * diffuse intensity
spec_exp = 4		# * specular reflection exponent
			#    (0 = diffuse only; > 50 = metallic)

tpi = 2 * pi
degs = 180 / pi
rads = pi / 180


def init():
	t = time.gmtime(time.time())
	y = t[0]
	m = t[1]
	d = t[2]
	h = t[3]
	mins = t[4]

	h = h + mins/60.
	return y, m, d, h

#   Get the days to J2000
#   h is UT in decimal hours
#   FNday only works between 1901 to 2099 - see Meeus chapter 7
def FNday (y, m, d, h):
	days = 367 * y - 7 * (y + (m + 9) // 12) // 4 + 275 * m // 9 + d - 730530 + h / 24.
	return float(days)

def rev(x):
	rv = x - int(x / 360) * 360
	if rv < 0: rv += 360
	return rv	

def calc_ra_dec(y, m, d, h):
	global L

	d = FNday(y, m, d, h)	

	w = 282.9404 + 4.70935E-5 * d
	a = 1.000000
	e = 0.016709 - 1.151E-9 * d 
	M = 356.0470 + 0.9856002585 * d
	M = rev(M)

	oblecl = 23.4393 - 3.563E-7 * d
	L = rev(w + M)

	E = M + degs * e * sin(M*rads) * (1 + e * cos(M*rads))

	x = cos(E*rads) - e
	y = sin(E*rads) * sqrt(1 - e*e)
	r = sqrt(x*x + y*y)
	v = atan2( y, x ) *degs
	lon = rev(v + w)

	xequat = r * cos(lon*rads) 
	yequat = r * sin(lon*rads) * cos(oblecl*rads)
	zequat = r * sin(lon*rads) * sin(oblecl*rads) 

	RA = atan2(yequat, xequat) * degs / 15
	Decl = asin(zequat / r) * degs

	return RA, Decl

def calc_alt(RA, Decl, lat, long, h):
	GMST0 = (L*rads + 180*rads) / 15 * degs
	SIDTIME = GMST0 + h + long/15
	HA = rev((SIDTIME - RA))*15

	x = cos(HA*rads) * cos(Decl*rads)
	y = sin(HA*rads) * cos(Decl*rads)
	z = sin(Decl*rads)

	xhor = x * sin(lat*rads) - z * cos(lat*rads)
	yhor = y
	zhor = x * cos(lat*rads) + z * sin(lat*rads)

	#azimuth = atan2(yhor, xhor)*degs + 180
	altitude = atan2(zhor, sqrt(xhor*xhor+yhor*yhor)) * degs

	return altitude

def im_name(n, res):
	return n + "_%ux%u" % (res[0], res[1]) + '.bmp'

def resize_images(size):
	for i in day, night:
		out = im_name(i, size)
		try: Image.open(out)
		except:
			x = Image.open(i + '.jpg')
			x2 = x.resize(size)
			x2.save(i + "_%ux%u" % (size[0], size[1]) + '.bmp')

def xy2ll(x, y, res):
	lat = 90. - float(y) / res[1] * 180.
	lon = float(x) / res[0] * 360. - 180.
	return lat, lon

def mixp(a, b, x):
	c = []
	for ai, bi in zip(a, b):
		c.append(int((1 - x) * ai + x * bi))
	return tuple(c)

def mul_tup(a, x):
	b = []
	for i in a:
		b.append(int(x * i))
	return tuple(b)

def plot(x, y, alt, width):
	ix = y * width + x
	if alt > blur and not phong:
		odat[ix] = ddat[ix]
	elif alt > blur:
		dc = ddat[ix]
		nc = ndat[ix]
		i = sin(rads * alt)
		shad_int = min(2., max(1.,
			shad_div / float(100. + dc[0] + dc[1] + dc[2])))
		shad_int *= (shad_int - .98)**.2	# reduce brightness in deserts
		odat[ix] = mul_tup(dc, 1. + .5 *
				(diff_int * i + i**spec_exp) * shad_int)
	elif alt < -blur:
		odat[ix] = ndat[ix]
	else:
		dc = ddat[ix]
		nc = ndat[ix]
		odat[ix] = mixp(nc, dc, (alt + blur) / blur / 2.)

def calc_image(name, res):
	global ddd, nnn, ddat, ndat, odat

	assert res[1] % 2 == 0, "Odd vertical resolutions not supported."

	resize_images(res)
	ddd = Image.open(im_name(day, res))
	nnn = Image.open(im_name(night, res))

	ddat = ddd.getdata()
	ndat = nnn.getdata()
	odat = res[0] * res[1] * [None]

	y, m, d, h = init()
	ra, dec = calc_ra_dec(y, m, d, h)
	hx = res[0] / 2
	hy = res[1] / 2

	for y in range(res[1] / 2):
		for x in range(res[0]):
			lat, lon = xy2ll(x, y, res)
			alt = calc_alt(ra, dec, lat, lon, h)
			plot(x, y, alt, res[0])	
			x2 = x + hx
			y2 = 2 * (hy - y) + y - 1
			if x2 > res[0] - 1: x2 -= res[0]
			plot(x2, y2, -alt, res[0])	
	ddd.putdata(odat)
	#ddd.save(name)
	ddd.save(name + '.jpg', quality = 85)		# also save as JPEG

try:
	import psyco
	psyco.full()
except ImportError: pass


if __name__ == '__main__':
	# test the algorithm for the current date:
	calc_image("rssplanet.png", (800, 600))
