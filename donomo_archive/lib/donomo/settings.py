"""
Django settings for the Donomo project.

"""

import os
import os.path
import platform
import logging
import sys

#
# pylint: disable-msg=W0142
#   W0142 - Used * or ** magic
#

# ---------------------------------------------------------------------------

def get_module_dir(module_name):
    """
    Helper function to get the directory in which a module is defined.
    Give the module by fully-qualified name (e.g., 'foo.bar.baz')

    """

    return os.path.dirname(__import__(module_name, {}, {}, ['']).__file__)


# ---------------------------------------------------------------------------

def join_and_normalize( *path_components ):
    """
    Helper function to combine os.path.join and os.path.normpath

    """
    return os.path.normpath(os.path.join(*path_components))

# ---------------------------------------------------------------------------
#
# Debugging Status
#

DEVELOPMENT_MODE = (platform.node() != 'web18.webfaction.com')
DEBUG            = DEVELOPMENT_MODE or os.environ.get('DEBUG', False)
TEMPLATE_DEBUG   = DEBUG
OS_USER_NAME     = os.environ.get('LOGNAME', None) or os.getlogin()

# ---------------------------------------------------------------------------
#
# Handy path shortcuts
#
# TODO: Figure out a nice strategy for setting paths for logs and caches
#

DONOMO_PATH = get_module_dir('donomo')
DJANGO_PATH = get_module_dir('django')
LOG_PATH    = os.environ.get('DONOMO_LOG_PATH', '.')
CACHE_PATH  = os.environ.get('DONOMO_CACHE_PATH', '/home/alexissmirnov/tmp/cache/')

# ---------------------------------------------------------------------------
#
# Info and credentials for external services
#
# TODO: Fix SOLR host information
#

AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID', '1GMGNJ65JN96A8BA6602')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'xdopAFEUuh0AHhOiR8eIP0MWiRiLsL1Svcy+zTjl')
S3_HOST               = os.environ.get('S3_HOST', 's3.amazonaws.com')
S3_IS_SECURE          = True
S3_BUCKET_PREFIX      = DEVELOPMENT_MODE and ("dev-%s." % OS_USER_NAME) or ''
S3_BUCKET             = '%sdata.donomo.com' % S3_BUCKET_PREFIX
SQS_HOST              = os.environ.get('SQS_HOST', 'queue.amazonaws.com')
SQS_IS_SECURE         = True
SOLR_HOST             = '127.0.0.1:8983'
S3_ACCESS_WINDOW      = 300

# ---------------------------------------------------------------------------
#
# Logging setup
#

LOGGING_PARAMS = {
    'format'  : '%(asctime)s %(name)s %(levelname)s [%(filename)s:%(lineno)d] %(module)s.%(funcName)s : %(message)s',
    }

if DEVELOPMENT_MODE:
    LOGGING_PARAMS.update( {
            'stream'   : sys.stderr,
            'level'    : logging.DEBUG,
            })
else:
    LOGGING_PARAMS.update( {
            'filename' : join_and_normalize(LOG_PATH, 'donomo.log'),
            'level'    : logging.INFO,
            })

if __name__ == 'donomo.settings':
    logging.basicConfig(**LOGGING_PARAMS)

logging.getLogger('boto').setLevel(logging.INFO)
logging.getLogger('S3').setLevel(logging.INFO)
logging.getLogger('SQS').setLevel(logging.INFO)

# ---------------------------------------------------------------------------
#
# Storage Settings
#
# [ Database, Cache, etc. ]
#

if DEVELOPMENT_MODE:
    DATABASE_ENGINE    = 'sqlite3'
    DATABASE_NAME      = join_and_normalize(DONOMO_PATH, 'donomo.db')
    DATABASE_USER      = None
    DATABASE_PASSWORD  = None
    MEDIA_ROOT         = join_and_normalize(DONOMO_PATH, 'archive/media/')
    ADMIN_MEDIA_PREFIX = '/admin_media/'
else:
    DATABASE_ENGINE    = 'mysql'
    DATABASE_NAME      = 'donomo'
    DATABASE_USER      = 'donomo'
    DATABASE_PASSWORD  = '8d85bcc668074be7ae4be08deae11705'
    MEDIA_ROOT         = '~/webapps/static/media/'
    ADMIN_MEDIA_PREFIX = 'http://smirnov.ca/media/'
    CACHE_BACKEND                   = "file://%s" % CACHE_PATH
    CACHE_MIDDLEWARE_SECONDS        = 60 * 5 # 5 minutes
    CACHE_MIDDLEWARE_KEY_PREFIX     = 'donomo'
    CACHE_MIDDLEWARE_GZIP           = True
    CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True


# ---------------------------------------------------------------------------
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
SECRET_KEY = os.environ.get('DONOMO_SECRET_KEY', 'gpx4_jy)xmr#z@%zqpnco@34s!#nb82003e2nv^k-kzc0m$x*z')

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
    'django_openidconsumer.middleware.OpenIDMiddleware',
    'donomo.archive.utils.yui.middleware.YUIIncludeMiddleware',
)

ROOT_URLCONF = 'donomo.urls'

TEMPLATE_DIRS = [
    os.path.normpath(path).replace('\\', '/') for path in (

        # This list comprehension will take care or normalizing the
        # path and replacing backslash characters with forward slash.
        # You just have to supply the absolute paths.

        os.path.join(DONOMO_PATH, 'templates'),
        os.path.join(DJANGO_PATH, 'contrib', 'admin', 'templates'),
        )
    ]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django_openidconsumer',
    'donomo.archive',
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

