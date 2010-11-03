# Maildir folder support
# Copyright (C) 2002 - 2007 John Goerzen
# <jgoerzen@complete.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import os.path, os, re, time, socket
from Base import BaseFolder
from offlineimap import imaputil
from offlineimap.ui import UIBase
from threading import Lock
from donomo.archive           import operations
from donomo.archive.models    import *

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

uidmatchre = re.compile(',U=(\d+)')
flagmatchre = re.compile(':.*2,([A-Z]+)')
timestampmatchre = re.compile('(\d+)');

timeseq = 0
lasttime = long(0)
timelock = Lock()

def on_savemessage(accountname, username, message_file, flags, label):
    print 'ON_SAVEMESSAGE: account=%s message file=%s flags=%s' % (username, message_file, flags)

    MODULE_NAME     = 'mail_parser' # os.path.splitext(os.path.basename(__file__))[0]
    DEFAULT_INPUTS  = [ AssetClass.UPLOAD ]
    DEFAULT_OUTPUTS = [ AssetClass.MESSAGE_PART ]
    DEFAULT_ACCEPTED_MIME_TYPES = [ MimeType.MAIL ]

    owner = User.objects.get(username=username)

    processor = operations.initialize_processor(
        MODULE_NAME,
        DEFAULT_INPUTS,
        DEFAULT_OUTPUTS,
        DEFAULT_ACCEPTED_MIME_TYPES ) [0]
    new_item = operations.create_asset_from_file(
        file_name    = message_file,
        owner        = owner,
        producer     = processor,
        asset_class  = AssetClass.UPLOAD,
        child_number = 0,
        mime_type    = MimeType.MAIL )
    new_item.orig_file_name += ',ACCOUNT=%s' % accountname
    new_item.orig_file_name += ',LABEL=%s' % label
    new_item.orig_file_name += ',FLAGS='
    for f in flags:
        new_item.orig_file_name += ',' + f
    new_item.save()
    operations.publish_work_item(new_item)

    return

def gettimeseq():
    global lasttime, timeseq, timelock
    timelock.acquire()
    try:
        thistime = long(time.time())
        if thistime == lasttime:
            timeseq += 1
            return (thistime, timeseq)
        else:
            lasttime = thistime
            timeseq = 0
            return (thistime, timeseq)
    finally:
        timelock.release()

class MaildirFolder(BaseFolder):
    def __init__(self, root, name, sep, repository, accountname, config):
        self.name = name
        self.config = config
        self.dofsync = config.getdefaultboolean("general", "fsync", True)
        self.root = root
        self.sep = sep
        self.messagelist = None
        self.repository = repository
        self.accountname = accountname
        BaseFolder.__init__(self)

    def getaccountname(self):
        return self.accountname

    def getfullname(self):
        return os.path.join(self.getroot(), self.getname())

    def getuidvalidity(self):
        """Maildirs have no notion of uidvalidity, so we just return a magic
        token."""
        return 42

    #Checks to see if the given message is within the maximum age according
    #to the maildir name which should begin with a timestamp
    def _iswithinmaxage(self, messagename, maxage):
        #In order to have the same behaviour as SINCE in an IMAP search
        #we must convert this to the oldest time and then strip off hrs/mins
        #from that day
        oldest_time_utc = time.time() - (60*60*24*maxage)
        oldest_time_struct = time.gmtime(oldest_time_utc)
        oldest_time_today_seconds = ((oldest_time_struct[3] * 3600) \
            + (oldest_time_struct[4] * 60) \
            + oldest_time_struct[5])
        oldest_time_utc -= oldest_time_today_seconds

        timestampmatch = timestampmatchre.search(messagename)
        timestampstr = timestampmatch.group()
        timestamplong = long(timestampstr)
        if(timestamplong < oldest_time_utc):
            return False
        else:
            return True


    def _scanfolder(self):
        """Cache the message list.  Maildir flags are:
        R (replied)
        S (seen)
        T (trashed)
        D (draft)
        F (flagged)
        and must occur in ASCII order."""
        retval = {}
        files = []
        nouidcounter = -1               # Messages without UIDs get
                                        # negative UID numbers.
        foldermd5 = md5(self.getvisiblename()).hexdigest()
        folderstr = ',FMD5=' + foldermd5
        for dirannex in ['new', 'cur']:
            fulldirname = os.path.join(self.getfullname(), dirannex)
            files.extend(os.path.join(fulldirname, filename) for
                         filename in os.listdir(fulldirname))
        for file in files:
            messagename = os.path.basename(file)

            #check if there is a parameter for maxage / maxsize - then see if this
            #message should be considered or not
            maxage = self.config.getdefaultint("Account " + self.accountname, "maxage", -1)
            maxsize = self.config.getdefaultint("Account " + self.accountname, "maxsize", -1)

            if(maxage != -1):
                isnewenough = self._iswithinmaxage(messagename, maxage)
                if(isnewenough != True):
                    #this message is older than we should consider....
                    continue

            #Check and see if the message is too big if the maxsize for this account is set
            if(maxsize != -1):
                filesize = os.path.getsize(file)
                if(filesize > maxsize):
                    continue


            foldermatch = messagename.find(folderstr) != -1
            if not foldermatch:
                # If there is no folder MD5 specified, or if it mismatches,
                # assume it is a foreign (new) message and generate a
                # negative uid for it
                uid = nouidcounter
                nouidcounter -= 1
            else:                       # It comes from our folder.
                uidmatch = uidmatchre.search(messagename)
                uid = None
                if not uidmatch:
                    uid = nouidcounter
                    nouidcounter -= 1
                else:
                    uid = long(uidmatch.group(1))
            flagmatch = flagmatchre.search(messagename)
            flags = []
            if flagmatch:
                flags = [x for x in flagmatch.group(1)]
            flags.sort()
            retval[uid] = {'uid': uid,
                           'flags': flags,
                           'filename': file}
        return retval

    def quickchanged(self, statusfolder):
        self.cachemessagelist()
        savedmessages = statusfolder.getmessagelist()
        if len(self.messagelist) != len(savedmessages):
            return True
        for uid in self.messagelist.keys():
            if uid not in savedmessages:
                return True
            if self.messagelist[uid]['flags'] != savedmessages[uid]['flags']:
                return True
        return False

    def cachemessagelist(self):
        if self.messagelist is None:
            self.messagelist = self._scanfolder()

    def getmessagelist(self):
        return self.messagelist

    def getmessage(self, uid):
        filename = self.messagelist[uid]['filename']
        file = open(filename, 'rt')
        retval = file.read()
        file.close()
        return retval.replace("\r\n", "\n")

    def getmessagetime( self, uid ):
        filename = self.messagelist[uid]['filename']
        st = os.stat(filename)
        return st.st_mtime

    def savemessage(self, uid, content, flags, rtime):
        # This function only ever saves to tmp/,
        # but it calls savemessageflags() to actually save to cur/ or new/.
        ui = UIBase.getglobalui()
        ui.debug('maildir', 'savemessage: called to write for %s  with flags %s uid %s rtime %s in %s and content %s' % \
                 (self.accountname, repr(flags), repr(uid), repr(rtime), repr(self.getvisiblename()), repr(content)))
        if uid < 0:
            # We cannot assign a new uid.
            return uid
        if uid in self.messagelist:
            # We already have it.
            self.savemessageflags(uid, flags)
            return uid

        # Otherwise, save the message in tmp/ and then call savemessageflags()
        # to give it a permanent home.
        tmpdir = os.path.join(self.getfullname(), 'tmp')
        messagename = None
        attempts = 0
        while 1:
            if attempts > 15:
                raise IOError, "Couldn't write to file %s" % messagename
            timeval, timeseq = gettimeseq()
            messagename = '%d_%d.%d.%s,U=%d,FMD5=%s' % \
                          (timeval,
                           timeseq,
                           os.getpid(),
                           socket.gethostname(),
                           uid,
                           md5(self.getvisiblename()).hexdigest())
            if os.path.exists(os.path.join(tmpdir, messagename)):
                time.sleep(2)
                attempts += 1
            else:
                break
        tmpmessagename = messagename.split(',')[0]
        ui.debug('maildir', 'savemessage: using temporary name %s' % tmpmessagename)
        file = open(os.path.join(tmpdir, tmpmessagename), "wt")
        file.write(content)

        # Make sure the data hits the disk
        file.flush()
        if self.dofsync:
            os.fsync(file.fileno())

        file.close()
        if rtime != None:
            os.utime(os.path.join(tmpdir,tmpmessagename), (rtime,rtime))
        ui.debug('maildir', 'savemessage: moving from %s to %s' % \
                 (tmpmessagename, os.path.join(tmpdir, messagename)))
        if tmpmessagename != messagename: # then rename it
            os.rename(os.path.join(tmpdir, tmpmessagename),
                    os.path.join(tmpdir, messagename))

        if self.dofsync:
            try:
                # fsync the directory (safer semantics in Linux)
                fd = os.open(tmpdir, os.O_RDONLY)
                os.fsync(fd)
                os.close(fd)
            except:
                pass

        self.messagelist[uid] = {'uid': uid, 'flags': [],
                                 'filename': os.path.join(tmpdir, messagename)}

        username = self.config.getdefault("Account " + self.accountname, "username", "")
        on_savemessage(self.accountname, username, os.path.join(tmpdir, messagename), flags, self.getvisiblename())

        self.savemessageflags(uid, flags)
        ui.debug('maildir', 'savemessage: returning uid %d' % uid)

        return uid


    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    def savemessageflags(self, uid, flags):
        oldfilename = self.messagelist[uid]['filename']
        newpath, newname = os.path.split(oldfilename)
        tmpdir = os.path.join(self.getfullname(), 'tmp')
        if 'S' in flags:
            # If a message has been seen, it goes into the cur
            # directory.  CR debian#152482, [complete.org #4]
            newpath = os.path.join(self.getfullname(), 'cur')
        else:
            newpath = os.path.join(self.getfullname(), 'new')
        infostr = ':'
        infomatch = re.search('(:.*)$', newname)
        if infomatch:                   # If the info string is present..
            infostr = infomatch.group(1)
            newname = newname.split(':')[0] # Strip off the info string.
        infostr = re.sub('2,[A-Z]*', '', infostr)
        flags.sort()
        infostr += '2,' + ''.join(flags)
        newname += infostr

        newfilename = os.path.join(newpath, newname)
        if (newfilename != oldfilename):
            os.rename(oldfilename, newfilename)
            self.messagelist[uid]['flags'] = flags
            self.messagelist[uid]['filename'] = newfilename

        # By now, the message had better not be in tmp/ land!
        final_dir, final_name = os.path.split(self.messagelist[uid]['filename'])
        assert final_dir != tmpdir

    def deletemessage(self, uid):
        if not uid in self.messagelist:
            return
        filename = self.messagelist[uid]['filename']
        try:
            os.unlink(filename)
        except OSError:
            # Can't find the file -- maybe already deleted?
            newmsglist = self._scanfolder()
            if uid in newmsglist:       # Nope, try new filename.
                os.unlink(newmsglist[uid]['filename'])
            # Yep -- return.
        del(self.messagelist[uid])

