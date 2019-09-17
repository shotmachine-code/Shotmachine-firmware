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
                return ""
            else:
                Username = result[0]
                return Username
        except:
            print("Unexpected error:", sys.exc_info()[0])
            self.db.rollback()
            return ""


    def ShotToDatabase(self, barcode, shot):
        sql_get_shot_id = "SELECT shot_id FROM party_has_shots WHERE(party_id={} AND tank_index = {});"
        sql_get_user_id = "SELECT id FROM users WHERE (barcode = {} AND party_id = {});"
        sql_write_shot = "INSERT INTO takenshots (datetime, shot_id, user_id, party_id, created_at, updated_at) VALUES (now(), %s, %s, %s,  now(), now());"
        try:
            self.cursor.execute(sql_get_shot_id.format(self.party_id, shot))
            shot_id = str(self.cursor.fetchone()[0])
            self.cursor.execute(sql_get_user_id.format(barcode, self.party_id))
            user_id = str(self.cursor.fetchone()[0])
            self.cursor.execute(sql_write_shot, (shot_id, user_id, str(self.party_id)))
            self.db.commit()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            self.db.rollback()

    #def pictureToDatabase(self):
