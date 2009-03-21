"""
Django settings for the Donomo project.

"""

import os
import platform
import logging
import sys
import tempfile
import pwd

#
# pylint: disable-msg=W0142
#   W0142 - Used * or ** magic
#
#

##############################################################################

def get_module_dir(module_name):
    """
    Helper function to get the directory in which a module is defined.
    Give the module by fully-qualified name (e.g., 'foo.bar.baz')

    """

    return os.path.dirname(__import__(module_name, {}, {}, ['']).__file__)


##############################################################################

def join_and_normalize( *path_components ):
    """
    Helper function to combine os.path.join and os.path.normpath

    """
    return os.path.normpath(os.path.join(*path_components))

##############################################################################

def query_env(
    variables,
    default = None,
    delete = None ):

    """ Helper function to query the environment for settings.

        If found the settings will be removed from the environment by default.
    """

    if delete is None:
        delete = os.environ.get('KEEP_ENVIRONMENT', 'no').lower() not in [ 'yes', 'true', '1', 'on' ]

    def retrieve( key ):
        value = os.environ.get(key, None)
        if delete and value is not None:
            del os.environ[key]
        return value

    if isinstance(variables, basestring):
        variables = [ variables ]

    value = None
    for name in variables:
        v1 = retrieve(name)
        v2 = retrieve('EC2_%s' % name.upper())
        if value is None:
            value = v1 or v2

    value = value or default

    if value is None:
        raise KeyError(
            'Environment: %s' % ', '.join(variables))

    return value

##############################################################################

def is_affirmative( flag ):
    return flag.lower() in ( 'true', 'on', 'yes', '1', 1 )


##############################################################################
#
# Debugging Status
#

DEPLOYMENT_MODE  = query_env( 'DEPLOYMENT_MODE', 'dev').lower()
TEST_MODE        = ( DEPLOYMENT_MODE.find('test') != -1 )
PRODUCTION_MODE  = ( DEPLOYMENT_MODE == 'prod' )
DEVELOPMENT_MODE = not (TEST_MODE or PRODUCTION_MODE)
OS_USER_NAME     = query_env( 'LOGNAME', pwd.getpwuid(os.getuid())[0])
TEMP_DIR         = query_env('TEMP_DIR', tempfile.gettempdir())

DEBUG            = DEVELOPMENT_MODE or is_affirmative(query_env('DEBUG','no'))
TEMPLATE_DEBUG   = DEBUG

##############################################################################
#
# Handy path shortcuts
#
# TODO: Figure out a nice strategy for setting paths for logs and caches
#

DONOMO_PATH = get_module_dir('donomo')
DJANGO_PATH = get_module_dir('django')
LOG_PATH    = query_env('DONOMO_LOG_PATH', '/var/log/donomo')
CACHE_PATH  = query_env('DONOMO_CACHE_PATH', '/var/lib/donomo/cache')

##############################################################################
#
# Info and credentials for external services
#

AWS_ACCESS_KEY_ID      = query_env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY  = query_env('AWS_SECRET_ACCESS_KEY')
AWS_MODE_PREFIX        = (TEST_MODE or DEVELOPMENT_MODE) and DEPLOYMENT_MODE or None
AWS_PREFIX             = query_env('AWS_PREFIX', PRODUCTION_MODE and '' or ("%s.%s." % (DEPLOYMENT_MODE, OS_USER_NAME)))

S3_HOST                = query_env('S3_HOST', 's3.amazonaws.com')
S3_IS_SECURE           = is_affirmative(query_env('S3_IS_SECURE', 'yes'))
S3_BUCKET_NAME         = '%sarchive.donomo.com' % AWS_PREFIX
S3_ACCESS_WINDOW       = int(query_env('S3_ACCESS_WINDOW', 300))

SQS_HOST               = query_env('SQS_HOST', 'queue.amazonaws.com')
SQS_IS_SECURE          = is_affirmative(query_env('SQS_IS_SECURE', 'yes'))
SQS_QUEUE_NAME         = '%sarchive-donomo-com' % AWS_PREFIX.replace('.', '-')
SQS_MAX_BACKOFF        = int(query_env('SQS_MAX_BACKOFF', 30))
SQS_VISIBILITY_TIMEOUT = int(query_env('SQS_VISIBILITY_TIMEOUT', 3600))

SOLR_HOST              = query_env('SOLR_HOST', '127.0.0.1')
SOLR_PORT              = int(query_env('SOLR_PORT', 8983))
SOLR_IS_SECURE         = is_affirmative(query_env('SOLR_IS_SECURE', 'no'))



# Thumbnail settings
THUMBNAIL_SIZE        = ( 340, 440 ) # 8.5" x 11.0" scaled to 40 ppi

##############################################################################
#
# Logging setup
#

LOGGING_PARAMS = {
    'format'  : '%(asctime)s %(levelname)s %(funcName)s (%(filename)s:%(lineno)d): %(message)s',
    }

if DEVELOPMENT_MODE:
    LOGGING_PARAMS.update( {
            'stream'   : sys.stderr,
            'level'    : logging.DEBUG,
            })
else:
    LOGGING_PARAMS.update( {
            'stream'   : sys.stderr,
            'level'    : logging.INFO,
            })

if __name__ == 'donomo.settings':
    logging.basicConfig(**LOGGING_PARAMS)

logging.getLogger('boto').setLevel(logging.INFO)

##############################################################################
#
# Storage Settings
#
# [ Database, Cache, etc. ]
#

DATABASE_ENGINE    = (DEPLOYMENT_MODE != 'unittest') and 'mysql' or 'sqlite3'
DATABASE_NAME      = 'donomo_%s' % DEPLOYMENT_MODE
DATABASE_USER      = 'donomo'
DATABASE_PASSWORD  = query_env('DATABASE_PASSWORD')
DATABASE_HOST      = query_env('DATABASE_HOST', '')
DATABASE_PORT      = query_env('DATABASE_PORT', '')

if DEVELOPMENT_MODE or TEST_MODE:
    MEDIA_ROOT         = join_and_normalize(DONOMO_PATH, 'archive', 'media/')
    ADMIN_MEDIA_PREFIX = '/admin_media/'
else:
    MEDIA_ROOT         = '~/webapps/static/media/'
    ADMIN_MEDIA_PREFIX = '/admin_media/'
    CACHE_BACKEND                   = "file://%s" % CACHE_PATH
    CACHE_MIDDLEWARE_SECONDS        = 60 * 5 # 5 minutes
    CACHE_MIDDLEWARE_KEY_PREFIX     = 'donomo'
    CACHE_MIDDLEWARE_GZIP           = True
    CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True


##############################################################################
#
# Database Settings
#


ADMINS = (
    ('Alexis Smirnov', 'alexis@donomo.com'),
    ('Roger McFarlane', 'roger@donomo.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name although not
# all choices may be avilable on all operating systems.  If running in
# a Windows environment this must be set to the same as your system
# time zone.

TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as
# not to load the internationalization machinery.
USE_I18N = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use
# a trailing slash if there is a path component (optional in other
# cases).  Examples: "http://media.lawrence.com",
# "http://example.com/media/"
MEDIA_URL = '/media/'


# Make this unique, and don't share it with anybody.
SECRET_KEY = query_env('SECRET_KEY', 'gpx4_jy)xmr#z@%zqpnco@34s!#nb82003e2nv^k-kzc0m$x*z')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.middleware.cache.CacheMiddleware',
    'donomo.archive.utils.middleware.AjaxErrorHandlingMiddleware',
    'donomo.archive.utils.yui.middleware.YUIIncludeMiddleware',
)

ROOT_URLCONF = 'donomo.urls'

TEMPLATE_DIRS = [
    os.path.normpath(path).replace('\\', '/') for path in (

        # This list comprehension will take care or normalizing the
        # path and replacing backslash characters with forward slash.
        # You just have to supply the absolute paths.

        os.path.join(DONOMO_PATH, 'archive', 'templates'),
        os.path.join(DJANGO_PATH, 'contrib', 'admin', 'templates'),
        )
    ]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'donomo.archive',
    'registration',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'donomo.archive.account.auth_backend.OpenIDAuthBackend',
    )

AUTH_PROFILE_MODULE = 'account.userprofile'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    )

APPEND_SLASH = False

ACCOUNT_ACTIVATION_DAYS=7 # Used by registration
DEFAULT_FROM_EMAIL='Donomo Registration <registration@donomo.com>'
UPLOAD_NOTIFICATION_EMAIL='Donomo Cloud OCR <registration.donomo.com>'
EMAIL_HOST_USER='registration@donomo.com'
EMAIL_HOST_PASSWORD='8d85bcc'
EMAIL_HOST='smtp.gmail.com'
EMAIL_PORT=587
EMAIL_USE_TLS=True

RECAPTCHA_DISABLED = True
RECAPTCHA_PUBLIC_KEY = "6LdwQwMAAAAAAGORYDLYzn9w8SniEL2X14o6SBNO"
RECAPTCHA_PRIVATE_KEY = "6LdwQwMAAAAAAJCZP67vaWH8WiDN5nkOT8pm2D9x"

BASIC_AUTH_REALM = 'donomo.com'
LOGIN_URL='/account/login/'
