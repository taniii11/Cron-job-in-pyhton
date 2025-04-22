import mysql.connector

def connect_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",   
            user="root",        
            password="",       
            database="admiral_db"  
        )
        return connection
    except mysql.connector.Error as err:
        print(f"❌ Database Connection Error: {err}")
        return None
