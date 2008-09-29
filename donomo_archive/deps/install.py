#! /usr/bin/env python


"""install.py - dependency install script.

Sample usage:

  python install.py zlib jpeg pil
  python install.py pil

  When adding a new dependency don't forget to update ALL_PACKAGES
"""


import os, string, sys
from os.path import basename, join
from urllib import urlopen



ALL_PACKAGES = ['recaptcha', 'jpeg', 'zlip', 'pil', 'tiff', 'elementtree', 'libpng', 'pypdf']

###############################################################################
# Package descriptions
###############################################################################

pysqllite = {
    "name": "pysqllite",
    "homepage": "http://oss.itsystementwicklung.de/trac/pysqlite/",
    "download" : "http://oss.itsystementwicklung.de/download/pysqlite/2.4/2.4.1/pysqlite-2.4.1.tar.gz",
    "install": """\
    """
}

recaptcha = {
    "name":     "recaptcha client",
    "homepage": "http://recaptcha.net/",
    "download": "http://pypi.python.org/packages/source/r/recaptcha-client/recaptcha-client-1.0.2.tar.gz",
    "install": """\
tar xfz recaptcha-client-1.0.2.tar.gz
cd ecaptcha-client-1.0.2
sudo python setup.py install
"""}


jpeg = {
    "name":     "JPEG Support for PIL",
    "homepage": "http://www.ijg.org",
    "download": "http://www.ijg.org/files/jpegsrc.v6b.tar.gz",
    "install": """\
tar xfz jpegsrc.v6b.tar.gz
cd jpeg-6b
./configure
make
make test
sudo make install
sudo make install-lib
"""}


zlib = {
    "name":     "Zlib",
    "homepage": "http://www.gzip.org/zlib/",
    "download": "http://www.gzip.org/zlib/zlib-1.2.3.tar.gz",
    "install": """\
tar xfz zlib-1.2.3.tar.gz
cd zlib-1.2.3
./configure
make
sudo make install
"""}


pil = {
    "name":     "PythonWare's PIL 1.1.6",
    "homepage": "http://www.pythonware.com/products/pil/",
    "download": "http://effbot.org/downloads/Imaging-1.1.6.tar.gz",
    "install": """\
tar xfz Imaging-1.1.6.tar.gz
cd Imaging-1.1.6
cd libImaging
./configure
make
cd ..
python setup.py build
sudo python setup.py install
"""}

tiff = {
    "name":     "TIFF library and utilities",
    "homepage": "http://www.libtiff.org",
    "download": "ftp://ftp.remotesensing.org/pub/libtiff/tiff-3.8.2.tar.gz",
    "install": """\
tar xfz tiff-3.8.2.tar.gz
cd tiff-3.8.2
./configure -with-ZIP
make
sudo make install
"""}

libpng = {
    "name":     "libPNG",
    "homepage": "http://www.libpng.org",
    "download": "http://download.sourceforge.net/libpng/libpng-1.2.29.tar.gz",
    "install": """\
tar xfz libpng-1.2.29.tar.gz
cd libpng-1.2.29
./configure
sudo make install
"""}

elementtree = {
    "name":     "ElementTree",
    "homepage": "http://effbot.org/zone/element-index.htm",
    "download": "http://effbot.org/media/downloads/elementtree-1.2.6-20050316.tar.gz",
    "install": """\
tar xfz elementtree-1.2.6-20050316.tar.gz
cd elementtree-1.2.6-20050316
sudo python setup.py install
"""}

pypdf = {
    "name":     "pyPDF",
    "homepage": "http://pybrary.net/pyPdf/",
    "download": "http://pybrary.net/pyPdf/pyPdf-1.11.tar.gz",
    "install": """\
tar xfz pyPdf-1.11.tar.gz
cd pyPdf-1.11
sudo python setup.py install
"""}


###############################################################################
# Installation
###############################################################################

def install(packages):
    dir = os.getcwd()

    for p in packages:
        try:
            p = globals()[p]
        except:
            print "Skipping", p
            continue

        # get package details
        name = p['name']
        url = p['download']
        homepage = p['homepage']
        instructions = p['install']

        # download, if needed
        path = join(dir, basename(url))
        if not os.path.exists(path):
            print "Downloading", name
            data = urlopen(url).read()
            open(path, "wb").write(data)

        # install
        print "Installing %s. See %s for details." % (name, homepage)
        open('install.sh', 'w').write(instructions)
        os.system('sh install.sh')




if __name__ == '__main__':
    packages = sys.argv[1:] or ALL_PACKAGES
    print "installing: " + str(packages)
    install(packages)
