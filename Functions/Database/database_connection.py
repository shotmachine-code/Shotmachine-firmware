import os
import sys
import time
import pymysql
import logging
import xml.etree.ElementTree as ET


class database_connection():

    def __init__(self):

        self.logger = logging.getLogger("Database_connection")
        self.party_id = 3

        try:
            xml_file_path = os.path.join(os.getcwd(), 'mysql_settings.xml')
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            for mysqlXML in root.findall('mysql'):
                if mysqlXML.get('name') == 'local':
                    self.localMysqlUser = mysqlXML.find('user').text
                    self.localMysqlPass = mysqlXML.find('password').text
                    self.localMysqlIP = mysqlXML.find('ip').text

            self.db = pymysql.connect(self.localMysqlIP, self.localMysqlUser, self.localMysqlPass, "shotmachine")
            self.cursor = self.db.cursor()
            self.cursor.execute("SELECT VERSION()")
            dbVersion = self.cursor.fetchone()
            self.logger.info("Connected to local database with version : %s " % dbVersion)
        except:
            self.logger.info('Error in starting database sync')
            raise






    def getUserName(self, barcode):
        sql_check_username = "Select name FROM users WHERE (barcode = {} AND party_id = {})"
        try:
            self.cursor.execute(sql_check_username.format(barcode, self.party_id))
            result = self.cursor.fetchone()
            if result == None:
                #print("User not found, scanned barcode: " + str(read_number))
                return ""
            else:
                Username = result[0]
                #print("Barcode scanner from user: " + Username + " With barcode: " + str(barcode))
                return Username
        except:
            #print("Unexpected error:", sys.exc_info()[0])
            self.db.rollback()
            #print("Error in sql")
            return ""

