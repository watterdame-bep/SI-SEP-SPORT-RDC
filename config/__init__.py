# Utiliser PyMySQL comme pilote MySQL (évite la compilation de mysqlclient sous Windows)
import pymysql
pymysql.install_as_MySQLdb()
