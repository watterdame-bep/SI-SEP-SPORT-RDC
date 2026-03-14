"""WSGI config for SI-SEP Sport RDC."""
# Utiliser PyMySQL comme pilote MySQL avant tout import Django (évite mysqlclient 2.2.1+)
import pymysql
pymysql.install_as_MySQLdb()

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()
