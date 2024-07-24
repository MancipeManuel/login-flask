import MySQLdb

try:
    connection = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd="",
        db="dataflas"
    )
    print("Connection a la base de datos flash")
    connection.close()
except MySQLdb.Error as e:
    print(f"Error connecting to MySQL: {e}")
