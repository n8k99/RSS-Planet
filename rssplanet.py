#!/usr/bin/env python

# RSS-Planet 1.4
#
# By
# Martin C. Doege, 2008-11-18

__version__ = "1.4"

import os, re, sys, math, time, urllib2
import rssparser
import webplanet
try: import Image
except: Image = None

## Feed processing options:
delay      = 900	# news fetching update interval (seconds)
only_once  = False	# get news only once and exit (get periodically if set to False)
draw_delay = 200	# xplanet/internal renderer drawing interval (seconds)
mindist    = 2.		# minimum distance for stories (degrees); set to zero to show all stories
maxlen     = 35		# maximum number of characters in story title
maxstories = 10		# maximum number of stories plotted per feed
mfile      = 'rssitems'	# location for marker file

## Rendering settings:
timestamp = True	# show time of last update
tspos     = -75, -40	# timestamp position (lat, lon): Antarctica -70, 0; Canada 70, -90
start_xplanet = True	# Launch xplanet on startup
min_size  = 1		#   minimum symbol size
max_size  = 8		#   maximum symbol size
			#     (set to min_size value to make all symbols the same size)
icons     = True	# use web site icons instead of circles as markers (experimental)
iconsize  = 20, 20	#   resize icons to this size
icontransp = True	#   make icons transparent
fontsize  = 11		# font size for headlines

## Map projection settings:
lat  = 0		# View for above this latitude circle
lon  = 0		# View for above this meridian
proj = "rectangular"	# Map projection used
radius = 54		# Earth radius in percentage of screen height

## Web page output:
web_output = False	# Generate web page (for use on a web server)
web_path   = "web"	# directory for the background image and the HTML;
			#  relative to working directory
web_size   = 950, 600	# image size for web output
web_render = True	# render the background image in Python; requires the PIL

# Standalone mode (runs only once, does not start or kill xplanet):
standalone = False

if web_render:
	import renderplanet

## Advanced settings:
verbose     = False	# print out activity (command line option '-v')
size_linear = False	#   scale symbol sizes linearly? (quadratic scaling if False)
remove_vowels = False	# remove vowels from within title words
			#  --to allow more words for the given character limit
			#    while keeping the text (mostly) intelligible; very cute hack!

# Some preset layouts:
layouts = {
 "--us" :	{
		"lat"  : 10		,
		"lon"  : -90		,
		"proj" : "orthographic"	,
		"tspos" : (-40, -110)	,
		},

 "--ameu" :	{
		"lat"  : 30		,
		"lon"  : -40		,
		"proj" : "orthographic"	,
		"tspos" : (-30, 0)	,
		},

 "--euas" :	{
		"lat"  : 20		,
		"lon"  : 40		,
		"proj" : "orthographic"	,
		"tspos" : (-25, -20)	,
		},

 "--asau" :	{
		"lat"  : 10		,
		"lon"  : 100		,
		"proj" : "orthographic"	,
		"tspos" : (-30, 60)	,
		},

 "--hemi" :	{
		"lat"  : 30		,
		"lon"  : 100		,
		"proj" : "ancient"	,
		"tspos" : (-90, 110)	,
		"radius" : 64		,
		},

 "--nh" :	{
		"lat"  : 89		,
		"lon"  : 50		,
		"proj" : "orthographic"	,
		"tspos" : (89, 180)	,
		"radius" : 49		,
		},
}

## The feed URLS. Feeds earlier in the list are prioritized.

feeds = [
 ["http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/world/rss.xml", "BBC News (World)", True],
 ["http://www.washingtonpost.com/wp-dyn/rss/world/index.xml", "Washington Post", True],
 ["http://rss.cnn.com/rss/cnn_topstories.rss", "CNN.com Top Stories", True],
 ["http://rss.news.yahoo.com/rss/topstories", "Yahoo! News Top Stories", True],
 ["http://rss.cnn.com/rss/cnn_world.rss", "CNN.com World", True],
 ["http://rss.news.yahoo.com/rss/world", "Yahoo! News World", True],
 ["http://rss.news.yahoo.com/rss/science", "Yahoo! News Science", True]
]

## NO CHANGES SHOULD BE NECESSARY BELOW THIS LINE. ##############################################
#################################################################################################

caps = (("Washington",	"Washington DC"),
	("Washington District of Columbia", "Washington DC"),
	("London",	"London UK"),
	("Berlin",	"Berlin Germany"),
	("Paris",	"Paris France"),
	("Vatican City", "Rome Italy"),
	("United Nations", "New York")
)

ignore_words = ("january", "february", "march", "april", "may", "june", "july", "august",
		"september", "october", "november", "december", "pictures", "depth", "paul",
		"the", "this", "news", "un", "home", "radio", "europe", "rugby", "union", "council",
		"africa", "asia", "america", "east", "west", "north", "south", "university", "island",
		"western", "eastern", "nothern", "southern", "am", "pm", "station", "big", "tam",
		"thomas", "wilson", "great", "atoll", "alert", "jackson", "national", "united")


def printout(x):
	if verbose:
		print x

def get_rss(u):
	o = []
	try:
		result = rssparser.parse(u)
		for item in result['items']:
			title = item.get('title', u"(none)")
			url  = item.get('link', u"(none)")
			o.append((url, title.encode('ascii', 'replace')))
		return o
	except:
		return []
	
def get_story(u):
	html = ""
	try:
		f = urllib2.urlopen(u)
		b = False
		for x in f.readlines():
			if "<body" in x or "<BODY" in x:
				b = True
			if b:
				html += x.strip() + ' * '
		html = re.sub("<a href=.*?</a>", '', html)
		html = re.sub("<A HREF=.*?</A>", '', html)
		html = re.sub("<script.*?</script>", '', html)
		html = re.sub("<SCRIPT.*?</SCRIPT>", '', html)
		html = re.sub("<form.*?</form>", '', html)
		html = re.sub("<FORM.*?</FORM>", '', html)
		return re.sub("<.*?>", '', html)
	except: return ""

def _start_word(w):
	try:	return w.upper() == w and len(w) > 1 and w[0].isalpha() and w[1] != '.' and w.lower() not in ignore_words
	except: return False

def _caps_not_in_title(w, t):
	if w.upper() == w:
		return w not in t
	else: return False

def guess_by_caps(t, title):
	o = ""
	addword = False
	count = 0
	for w in t.split():
		count += 1
		if _start_word(w) and _caps_not_in_title(w, title) and not addword:
			addword = True
			count = 0
			o = ""
		if w == '--' or w == '-' and addword:
			addword = False
			return o.strip()
		if count > 4 or w == '*':
			addword = False
			o = ""
		if addword and w[0] != '(':
			o += w + ' '
	return o.strip()

def _in_cities_list(x):
	q = " %s " % x.lower()
	for c in cities:
		if q in c.lower():
			return True
	return False

def _start_word_all(w):
	return w[0].isupper() and len(w) > 1 and w.lower() not in ignore_words and _in_cities_list(w)

def guess_by_in(t, title):
	found = False
	o = ""
	for v in t.split():
		w = mk_alnum(v)
		if w == 'the': continue
		if found:
			if _start_word_all(w):
				o += w + ' '
			else:
				if o: return o.strip()
				else: found = False
		if w.lower() in ('in', 'to'):
			found = True

	for w in title:
			if w.upper() != w and _start_word_all(w):
				return w

	for v in t.split():
		w = mk_alnum(v)
		if _start_word_all(w):
			found = True
		if found:
			if _start_word_all(w):
				o += w + ' '
			else:
				return o.strip()

def text2place(t, title):
	c = guess_by_caps(t, title) or guess_by_in(t, title) or ""
	c = mk_alnum(c).strip()
	for x, y in caps:
		if c.lower() == x.lower():
			c = y
	q = ""
	for x in c.split():
		q += (abbrev.get(x.lower(),
			abbrev.get(x.lower() + '.',
				x)) + ' ')
	return q.strip()

def num2blank(x):
	if x.isalpha(): return x
	else: return ' '

def mk_alnum(p):
	p = [num2blank(x) for x in p if x.isalnum() or x == ' ']
	try: return reduce(lambda x, y: x + y, p)
	except: return ' '

def place2coord(p):
	p = mk_alnum(p)
	maxscore = 0
	o = ""
	for line in cities:
		l = line.lower()
		score = 0
		p2 = [x for x in p.split() if len(x) > 1]
		scores = range(len(p2), 0, -1)
		scores[-1] = scores[0]
		for x, s in zip(p2, scores):
			for w in l.split():
				w2 = w.strip()
				if x.lower() == w2:
					score += s
					if score > maxscore:
						o = l
						maxscore = score
	x = o.split(':')
	lat = float(x[3]) + float(x[4]) / 60.
	lon = float(x[7]) + float(x[8]) / 60.
	if x[6].strip()  == 's': lat = -lat
	if x[10].strip() == 'w': lon = -lon
	return lat, lon

def getdist(a, b):
	return math.sqrt( (a[0] - b[0]) * (a[0] - b[0]) +
			  (a[1] - b[1]) * (a[1] - b[1])  )

def store_item(c, t, u):
	global items, dropcount
	if mindist:
		for x in items:
			d = getdist(x[0], c)
			if d < mindist:
				printout("(dropped)")
				dc = dropcount.get(x[1], 0)
				dropcount[x[1]] = dc + 1
				printout("*** %s %u" % (x[1], dropcount[x[1]]))
				return
        t = [x for x in t if x.isalnum() or x in " ,:;.-+'!?$%/"]
        t = reduce(lambda x, y: x + y, t)
	items += (c, t, u),

def _devowel_word(x):
	#if x[0].isupper(): return x
	z = x[1:len(x) - 1]
	p = [y for y in z if y not in "aeiou"]
	try: return x[0] + reduce(lambda x, y: x + y, p) + x[-1]
	except: return x[0] + x[-1]

def devowel(t):
	o = ""
	for x in t.split():
		if len(x) > 2:
			o += _devowel_word(x) + ' '
		else:
			o += x + ' '
	return o.strip()

def gettrans(f):
	try:
		if not icontransp: return ''
		i = Image.open(f + ".png")
		r, g, b = list(i.convert("RGB").getdata())[0]
		return "transparent={%u,%u,%u}" % (r, g, b)
	except:
		return ''

def write_marker_file():
	if not items: return
	f = open(mfile, 'w')
	for c, t, u in items:
		if size_linear: v = dropcount.get(t, 0)
		else: v = math.sqrt(dropcount.get(t, 0))
		size = "%u" % min(max_size, min_size + v)
		if remove_vowels:
			t = devowel(t)
		if len(t) > maxlen:
			t = t[:maxlen] + "..."
		t = t.replace('"', "'")
		if web_output: t = ''
		if icons and Image != None:
			homeurl = re.compile("http://([^/]+)/").match(u).expand("\g<0>")
			dir = os.getcwd()
			fn = mk_alnum(homeurl).strip()
			try: Image.open(fn + ".png")
			except:
				try:
					ico = urllib2.urlopen(homeurl + "favicon.ico").read(5000)
					g = open(fn + ".ico", "wb")
					g.write(ico)
					g.close()
					i = Image.open(fn + ".ico")
					if iconsize:
						i.thumbnail(iconsize)
					i.save(fn + ".png")
				except:
					f.write('%f %f "%s" color=Yellow image=smile.png\n' % (c[0], c[1], t))
				else:
					f.write('%f %f "%s" color=Yellow image=%s.png %s\n' %
									(c[0], c[1], t, os.path.join(dir, fn), gettrans(fn)))
			else:
				f.write('%f %f "%s" color=Yellow image=%s.png %s\n' %
									(c[0], c[1], t, os.path.join(dir, fn), gettrans(fn)))
		else:
			f.write('%f %f "%s" color=Yellow symbolsize=%s\n' % (c[0], c[1], t, size))
	if timestamp:
		tl = time.strftime("%Y-%m-%d %H:%M %Z", time.localtime(time.time()))
		f.write('%f %f "Last updated %s" color=Green image=none align=above\n' % (
									tspos[0], tspos[1], tl))
	f.close()
	if web_output:
		f = open(os.path.join(web_path, "rssplanet.html"), 'w')
		webplanet.output_html(f, items, web_size, iconsize, web_path = web_path, mfile = mfile)
		f.close()
		if web_render: inline_render()		

def update():
	for f, n, status in feeds:
		if not status: continue
		printout(60 * '-')
		news = get_rss(f)			# returns a list of URLs and story titles
		for url, title in news[:maxstories]:
			try:
				text  = get_story(url)		# gets text for story
				place = text2place(text, title)	# find out the place name
				printout("%s -> %s" %(place, title))
				coord = place2coord(place)
				printout(coord)
				store_item(coord, title, url)	# remember item for later output
			except:
				printout("Warning, malformed story.")

def launch_xplanet():
	if not standalone:
		try: os.system("killall xplanet 2> /dev/null")
		except: pass
	if start_xplanet:
		#os.system("xplanet -wait 10 -fork -window -geometry 1024x768 -projection rectangular -config ./default")
		if sys.platform == 'win32':
			prog_name = "start /min xplanet.exe"
			redir     = ''
		else:
			prog_name = 'xplanet'
			redir     = "2> /dev/null"
		if not web_output:
			os.system("%s -wait %u  -projection %s -latitude %i -longitude %i -radius %u -fontsize %u -config ./default %s &"
				% (prog_name, draw_delay, proj, lat, lon, radius, fontsize, redir))
		elif not web_render:
			os.system("%s -output %s -geometry %ux%u -wait %u -projection %s -latitude %i -longitude %i -radius %u -fontsize %u -config ./default %s &"
				% (prog_name, os.path.join(web_path, 'rssplanet.png'), web_size[0], web_size[1],
					draw_delay, "rectangular", 0, 0, radius, fontsize, redir))

def inline_render():
	renderplanet.calc_image(os.path.join(web_path, 'rssplanet.png'), web_size)		


# check for command line options:
if "-w" in sys.argv or "--web" in sys.argv:
	web_output = True
if "-s" in sys.argv or "--standalone" in sys.argv:
	standalone = True
	web_output = False
	start_xplanet = False
	only_once  = True
if "-x" in sys.argv or "--web" in sys.argv:
	only_once  = True
if "-v" in sys.argv or "--verbose" in sys.argv:
	verbose = True
if "-h" in sys.argv or "--help" in sys.argv:
	print "Available presets:"
	for l in layouts.keys(): print l
	sys.exit(0)
for x in layouts.keys():
	if x in sys.argv:
		for y in layouts[x].keys():
			globals()[y] = layouts[x][y]

# read cities database:
f = open("Cities.dat", 'r')
cities = []
for x in f.readlines():
	cities.append(" %s " % x)
f.close()

# read abbreviations:
f = open("abbrev.dat", 'r')
abbrev = {}
for x in f.readlines():
	a, b = x.split(':')
	abbrev[b.lower().strip()] = a.strip()
f.close()

lastupd = 0

if __name__ == '__main__':
	launch_xplanet()
	while True:
		if time.time() - lastupd > delay:
			items = []
			dropcount = {}
			update()
			write_marker_file()		# generate the marker file
			printout("\n\n\n\n")
			lastupd = time.time()
		elif web_render: inline_render()
		if only_once: sys.exit(0)		
		time.sleep(draw_delay)
