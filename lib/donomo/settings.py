
import os
import os.path
import platform
import docstore
import logging
import sys

# Django settings for vault project.

AWS_ACCESS_KEY_ID='1GMGNJ65JN96A8BA6602'
AWS_SECRET_ACCESS_KEY='xdopAFEUuh0AHhOiR8eIP0MWiRiLsL1Svcy+zTjl'
S3_HOST='s3.amazonaws.com'
S3_IS_SECURE=False
S3_BUCKET='vault.%s.smirnov.ca' % os.environ.get('LOGNAME') or os.getlogin()
SQS_HOST='queue.amazonaws.com'
SQS_IS_SECURE=False
SOLR_HOST='127.0.0.1:8983'

# Determine if we're running on deployment server
DEVELOPMENT_MODE = (platform.node() != 'web18.webfaction.com')


if DEVELOPMENT_MODE:
    DEBUG = True
    DATABASE_ENGINE = 'sqlite3'
    DATABASE_NAME = os.path.split(docstore.__file__)[0] + '/docstore.db'
    MEDIA_ROOT = os.path.split(docstore.__file__)[0] + '/media/'
    S3_BUCKET="dev." + S3_BUCKET
    TEMPLATE_DIRS = (
        os.path.split(docstore.__file__)[0] + '/templates',
    )
    ADMIN_MEDIA_PREFIX = '/admin_media/'
    if __name__ == 'docstore.settings':
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.DEBUG,
            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s [%(filename)s:%(lineno)d] %(module)s.%(funcName)s : %(message)s',
            datefmt='%H:%M:%S')
else:
    DATABASE_ENGINE = 'mysql'
    DATABASE_NAME = 'alexissmirnov_dj'
    DATABASE_USER = 'alexissmirnov_dj'
    DATABASE_PASSWORD = '99da604e'

    DEBUG = False
    MEDIA_ROOT = '~/webapps/static/media/'
    TEMPLATE_DIRS = (
        os.path.split(docstore.__file__)[0] + '/templates',
        '~/lib/python2.5/django/contrib/admin/templates/',
    )
    ADMIN_MEDIA_PREFIX = 'http://smirnov.ca/media/'

    CACHE_BACKEND = "file:///home/alexissmirnov/tmp/cache/vault/"
    CACHE_MIDDLEWARE_SECONDS = 60 * 5 # 5 minutes
    CACHE_MIDDLEWARE_KEY_PREFIX = 'vault'
    CACHE_MIDDLEWARE_GZIP = True
    CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

    if __name__ == 'docstore.settings':
        logging.basicConfig(filename='/home/alexissmirnov/logs/user/vault.log', level=logging.INFO,
               format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
               datefmt='%H:%M:%S')

SOLR_HOST="127.0.0.1:8983"


TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Alexis Smirnov', 'alexis@smirnov.ca'),
    ('Roger McFarlane', 'roger.mcfarlane@gmail.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.

TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'


# Make this unique, and don't share it with anybody.
SECRET_KEY = 'gpx4_jy)xmr#z@%zqpnco@34s!#nb82003e2nv^k-kzc0m$x*z'

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
)

ROOT_URLCONF = 'docstore.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.normpath(os.path.join(os.path.dirname(docstore.__file__), 'templates')).replace('\\', r'/'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django_openidconsumer',
    'docstore.core',
    'docstore.apps.account',
    'django_openidconsumer',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'docstore.apps.account.OpenIDAuthBackend',
    )

AUTH_PROFILE_MODULE = 'account.userprofile'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    
    )

