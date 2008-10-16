#!/usr/bin/env python
"""Upload file to donomo"""
from __future__ import with_statement 
import os
from optparse import OptionParser
import mimetypes, mimetools
import httplib2
import socket

VERSION = "$Rev:$"

h = httplib2.Http()

def post_multipart(url, files, fields=[]):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(files, fields)
    headers = {'User-Agent' : 'Donomo Desktop Uploader ' + VERSION,
               'Content-Type': content_type,
               'Content-Length': str(len(body))}
    try:
        r, c = h.request(url, 'POST', body, headers)
        print r.status
        print c
        return r.status == 202
        
    except Exception, e:
        print str(e)
        return False

def encode_multipart_formdata(files, fields = []):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = mimetools.choose_boundary()
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'



def main():
    parser = OptionParser(usage="""%prog <options> <files>. %prog -h for details.""")
    parser.add_option("-u", "--user", help="User's email address", dest="user")
    parser.add_option("-p", "--password", help="User's password", dest="password")
    parser.add_option("-d", "--delete", help="Delete files after they were uploaded", dest="delete", default=False, action="store_true", )
    parser.add_option("--domain", help="Domain name of the donomo server. May include port number after :", dest="domain", default="donomo.com" )
    
    (options, files) = parser.parse_args()

    if len(files) == 0:
        parser.print_usage()
        return
    
    print "Uploading %s to %s for %s" % (files, options.domain, options.user)

    for file_to_upload in files:
        with open(file_to_upload, 'rb') as f:
            print "Uploading %s ..." % file_to_upload
            uploaded = post_multipart("http://%s/api/1.0/documents/" % options.domain, 
                                      ((file_to_upload, file_to_upload, f.read()),), 
                                      (('user', options.user), ('password', options.password),))
        print "Uploaded? %s" % uploaded
            
        if options.delete and uploaded:
            os.remove(file_to_upload)
          

if __name__ == '__main__':
    main()
