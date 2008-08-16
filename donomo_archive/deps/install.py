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



ALL_PACKAGES = ['jpeg', 'zlip', 'pil', 'tiff', 'yadis', 'urljr', 'openid', 'elementtree', 'libpng']

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

yadis = {
    "name":     "Yadis for OpenID support",
    "homepage": "http://www.openid.org",
    "download": "http://openidenabled.com/files/python-openid/files/python-yadis-1.1.0.tar.gz",
    "install": """\
tar xfz python-yadis-1.1.0.tar.gz
cd python-yadis-1.1.0
sudo python setup.py install
"""}

urljr = {
    "name":     "Urljr for OpenID support",
    "homepage": "http://www.openid.org",
    "download": "http://openidenabled.com/files/python-openid/files/python-urljr-1.0.1.tar.gz",
    "install": """\
tar xfz python-urljr-1.0.1.tar.gz
cd python-urljr-1.0.1
sudo python setup.py install
"""}

openid = {
    "name":     "OpenID support",
    "homepage": "http://www.openid.org",
    "download": "http://openidenabled.com/files/python-openid/packages/python-openid-1.2.0.tar.gz",
    "install": """\
tar xfz python-openid-1.2.0.tar.gz
cd python-openid-1.2.0
sudo python setup.py install
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

#
#foursuite = {
#    "name":     "4Suite XPath support",
#    "homepage": "http://4suite.org",
#    "download": "ftp://ftp.4suite.org/pub/4Suite/4Suite-XML-1.0.2.tar.gz",
#    "install": """\
#tar xfz 4Suite-XML-1.0.2.tar.gz
#cd 4Suite-XML-1.0.2
#sudo python setup.py install
#"""}


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
