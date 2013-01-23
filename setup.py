#!/usr/bin/env python

from distutils.core import setup

setup(name="rssplanet",
        version="1.4.1",
        description="An RSS/RDF/Atom newsmapper for xplanet and OSXplanet",
        author="Martin C. Doege",
        author_email="mdoege@compuserve.com",
	url="http://home.arcor.de/mdoege/rssplanet/",
        py_modules=["rssparser"],
	scripts=["rssplanet.py", "planetgui.py", "webplanet.py", "renderplanet.py"],
	data_files=[
		('web/', ['wz_tooltip.js']),
		('./', ['Cities.dat']),
		('./', ['abbrev.dat']),
		('./', ['default'])
	] )
