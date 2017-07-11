#!/pkg/qct/software/python/3.5.2/bin/python

###############################################################################
# SQL Connection to Helium.qualcomm.com\Helium:49167
#https://docs.microsoft.com/en-us/azure/sql-database/sql-database-develop-python-simple
#
# csk - This is how to connect to the Helium DB. Change "import setup.sql_setup as sql_setup" in 
#   the python files to "import helium_db" and change the files to call 
#   "opendb()" and "closedb(db)" from "sql_setup" to "helium_db"
###############################################################################
import pymssql      #used for the db connection and sql actions

def opendb():
  try:
    # Open database connection
    db = pymssql.connect(server="helium.qualcomm.com",user="NA\user_name",password="password",port=49167,database="Helium")
  except:
    print ("ERROR: Could not make a connection to the database\n")
    raise
  # prepare a cursor object using cursor() method
  cursor = db.cursor()
  return db,cursor
  


# specify the database to use
#Not needed when database is specified in pymssql.connect()
#cursor.execute("use Helium;")

def closedb(db):
  db.close()
