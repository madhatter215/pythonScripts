#!/pkg/qct/software/python/3.5.2/bin/python

###############################################################################
# SQL Connection to Helium.qualcomm.com\Helium:49167
#https://docs.microsoft.com/en-us/azure/sql-database/sql-database-develop-python-simple
###############################################################################
import pymssql      #used for the db connection and sql actions

def opendb():
  try:
    # Open database connection
    connection = pymssql.connect(server="helium.qualcomm.com",user="NA\fakeuser",password="BOGUS",port=99999,database="Helium")
  except:
    print ("ERROR: Could not make a connection to the database\n")
    raise
  # prepare a cursor object using cursor() method
  cursor = connection.cursor()
  return connection,cursor
  


# specify the database to use
#Not needed when database is specified in pymssql.connect()
#cursor.execute("use Helium;")

def closedb(connection,cursor):
  cursor.close()
  connection.close()
