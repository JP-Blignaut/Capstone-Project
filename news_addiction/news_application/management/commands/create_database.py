import os
import mysql.connector
from mysql.connector import Error
from django.core.management.base import BaseCommand
from datetime import date
from dotenv import load_dotenv



class Command(BaseCommand):
    """Create the database for the news application
       This will drop the existing database and create a new one.
       Usage:
       python manage.py create_database
    
    """
    help = 'Create the database for the news application'
    load_dotenv()  # Load environment variables from .env file
    def create_connection(self):
        connection = None
        try:
            connection = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user="root",
                password="",
            )
            print("Connection to MySQL DB successful")
        except Error as e:
            print(f"The error '{e}' occurred")
        return connection

    def execute_query(self, connection, query):
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            connection.commit()
            print(f"{query} \nQuery executed successfully")
        except Error as e:
            print(f"The error '{e}' occurred")
            
    def recreate_database(self):
        connection = self.create_connection()
        drop_database_query = f"DROP DATABASE IF EXISTS `{os.getenv("DB_NAME")}`"
        self.execute_query(connection, drop_database_query)

        create_database_query = (f"CREATE DATABASE IF NOT EXISTS "
                                f"`{os.getenv("DB_NAME")}`")
        self.execute_query(connection, create_database_query)

        create_user_query = (f"CREATE USER IF NOT EXISTS '{os.getenv("DB_USER")}"
            f"'@'localhost' IDENTIFIED BY '{os.getenv("DB_PASSWORD")}'")

        self.execute_query(connection, create_user_query)
        grant_privileges_query = (
            f"GRANT ALL PRIVILEGES ON `{os.getenv("DB_NAME")}`.*"
            f" TO '{os.getenv("DB_USER")}'@'localhost'")
        self.execute_query(connection, grant_privileges_query)

        flush_privileges_query = "FLUSH PRIVILEGES"
        self.execute_query(connection, flush_privileges_query)

        connection.close()

    def handle(self, *args, **options):
        """
        Create default database for the news application
        """
        self.recreate_database()