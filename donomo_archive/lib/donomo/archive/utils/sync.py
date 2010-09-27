from __future__ import with_statement
from django.conf                     import settings
from donomo.archive                  import models

import ConfigParser
import StringIO
import os

def update_sync_config(account):
    """
    Updates the configuration of the module responsible for
    syncing content with the remote service.

    Currently only supports gmail
    """
    if account.account_class.name != models.AccountClass.EMAIL_GMAIL:
        return False

    config = ConfigParser.RawConfigParser()
    config.read(settings.OFFLINEIMAP_CONFIG_FILE)

    account_name = '%s.%s' % (account.owner.username, account.name)
    accounts = StringIO.StringIO()

    existing_accounts = config.get('general', 'accounts')
    if len(existing_accounts) > 0:
        accounts.write('%s,' % (account_name) )
        accounts.write(config.get('general', 'accounts'))
    else:
        accounts.write('%s' % (account_name) )

    config.set('general', 'accounts', accounts.getvalue())

    section_name = 'Account %s' % account_name
    config.add_section(section_name)
    config.set(section_name, 'localrepository', '%s.local' % account_name)
    config.set(section_name, 'remoterepository', '%s.remote' % account_name)
    config.set(section_name, 'username', account.owner.username)
    config.set(section_name, 'autorefresh', '1')

    # When you are starting to sync an already existing account yuo can tell offlineimap
    # to sync messages from only the last x days. When you do this messages older than x
    # days will be completely ignored. This can be useful for importing existing accounts
    # when you do not want to download large amounts of archive email.

    # Messages older than maxage days will not be synced, their flags will
    # not be changed, they will not be deleted etc. For offlineimap it will be like these
    # messages do not exist. This will perform an IMAP search in the case of IMAP or Gmail
    # and therefor requires that the server support server side searching. This will
    # calculate the earliest day that would be included in the search and include all
    # messages from that day until today. e.g. maxage = 3 to sync only the last 3 days mail
    # config.set(section_name, 'maxage', '10')

    section_name = 'Repository %s.local' % account_name
    config.add_section(section_name)
    config.set(section_name, 'type', 'Maildir')
    config.set(section_name, 'localfolders', '%s/%s' % (settings.OFFLINEIMAP_DATA_DIR, account_name))

    section_name = 'Repository %s.remote' % account_name
    config.add_section(section_name)
    config.set(section_name, 'type', 'Gmail')
    config.set(section_name, 'remoteuser', account.name)
    config.set(section_name, 'remotepass', account.password)

    # Writing our configuration file
    with open(settings.OFFLINEIMAP_CONFIG_FILE, 'wb') as configfile:
        config.write(configfile)

    #reload_offlineimap()

    return True

def reload_offlineimap():
    status = os.system('service offlineimap restart')

