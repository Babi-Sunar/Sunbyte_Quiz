"""
Django settings for the SunByte Quiz project.
"""

import os
from pathlib import Path
import dj_database_url
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------
# SECURITY
# -----------------------------------------------------------------------
# NEVER hard-code the secret key or DB password in real deployments.
# Both are read from environment variables, with safe local defaults
# only for quick local development.
# SECRET_KEY = os.environ.get(
#     'DJANGO_SECRET_KEY',
#     'django-insecure-change-this-in-production-!!!'
# )
SECRET_KEY = config('SECRET_KEY')

# DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
# ALLOWED_HOSTS = ['*']
# ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.7']
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

# -----------------------------------------------------------------------
# APPLICATION DEFINITION
# -----------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'quizapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sunbyte_quiz.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sunbyte_quiz.wsgi.application'

# -----------------------------------------------------------------------
# DATABASE  (MySQL)
# -----------------------------------------------------------------------
# Install the driver with:  pip install mysqlclient
# Create the database first, e.g.:
#   CREATE DATABASE quiz_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': os.environ.get('DB_NAME', 'quiz_db'),
#         'USER': os.environ.get('DB_USER', 'root'),
#         'PASSWORD': os.environ.get('DB_PASSWORD', '#itmp123!STD'),
#         'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
#         'PORT': os.environ.get('DB_PORT', '3306'),
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#         },
#     }
# }

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
    )
}

# -----------------------------------------------------------------------
# PASSWORD VALIDATION
# -----------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    # {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -----------------------------------------------------------------------
# INTERNATIONALIZATION
# -----------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------
# STATIC & MEDIA FILES
# -----------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# -----------------------------------------------------------------------
# AUTH
# -----------------------------------------------------------------------
LOGIN_URL = 'quizapp:login'
LOGIN_REDIRECT_URL = 'quizapp:dashboard'
LOGOUT_REDIRECT_URL = 'quizapp:home'


# qr code generation settings
"""
Django settings for the SunByte Quiz project.
"""

import os
from pathlib import Path
import dj_database_url
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------
# SECURITY
# -----------------------------------------------------------------------
# NEVER hard-code the secret key or DB password in real deployments.
# Both are read from environment variables, with safe local defaults
# only for quick local development.
# SECRET_KEY = os.environ.get(
#     'DJANGO_SECRET_KEY',
#     'django-insecure-change-this-in-production-!!!'
# )
SECRET_KEY = config('SECRET_KEY')

# DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
# ALLOWED_HOSTS = ['*']
# ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.7']
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

# -----------------------------------------------------------------------
# APPLICATION DEFINITION
# -----------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'quizapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sunbyte_quiz.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sunbyte_quiz.wsgi.application'

# -----------------------------------------------------------------------
# DATABASE  (MySQL)
# -----------------------------------------------------------------------
# Install the driver with:  pip install mysqlclient
# Create the database first, e.g.:
#   CREATE DATABASE quiz_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': os.environ.get('DB_NAME', 'quiz_db'),
#         'USER': os.environ.get('DB_USER', 'root'),
#         'PASSWORD': os.environ.get('DB_PASSWORD', '#itmp123!STD'),
#         'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
#         'PORT': os.environ.get('DB_PORT', '3306'),
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#         },
#     }
# }

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
    )
}

# -----------------------------------------------------------------------
# PASSWORD VALIDATION
# -----------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    # {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -----------------------------------------------------------------------
# INTERNATIONALIZATION
# -----------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------
# STATIC & MEDIA FILES
# -----------------------------------------------------------------------
# STATIC_URL = 'static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# STATICFILES_DIRS = [BASE_DIR / 'static']
# STATIC_ROOT = BASE_DIR / 'staticfiles'

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# -----------------------------------------------------------------------
# AUTH
# -----------------------------------------------------------------------
LOGIN_URL = 'quizapp:login'
LOGIN_REDIRECT_URL = 'quizapp:dashboard'
LOGOUT_REDIRECT_URL = 'quizapp:home'





# CLOUDINARY
import os

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": os.environ.get("CLOUDINARY_API_KEY"),
    "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET"),
}

# STORAGES = {
#     "default": {
#         "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
#     },
#     "staticfiles": {
#         "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
#     },
# }


RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

DEFAULT_FROM_EMAIL = "SunByte Quiz <onboarding@resend.dev>"