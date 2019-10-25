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
            xml_file_path = os.path.join(os.getcwd(), 'settings.xml')
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            for mysqlXML in root.findall('mysql'):
                if mysqlXML.get('name') == 'mysql_local':
                    self.localMysqlUser = mysqlXML.find('user').text
                    self.localMysqlPass = mysqlXML.find('password').text
                    self.localMysqlIP = mysqlXML.find('ip').text
                if mysqlXML.get('name') == 'mysql_online':
                    self.onlineMysqlUser = mysqlXML.find('user').text
                    self.onlineMysqlPass = mysqlXML.find('password').text
                    self.onlineMysqlIP = mysqlXML.find('ip').text

            #self.db = pymysql.connect(self.localMysqlIP, self.localMysqlUser, self.localMysqlPass, "shotmachine")
            #cursor = self.db.cursor()
            #cursor.execute("SELECT VERSION()")
            #dbVersion = cursor.fetchone()
            #cursor.close()
            #self.logger.info("Connected to local database with version : %s " % dbVersion)
            #db.close()

        except:
            self.logger.info('Error in reading database settings')
            raise


    def getUserName(self, barcode):
        sql_check_username = "Select name FROM users WHERE (barcode = {} AND party_id = {})"
        try:
            db = pymysql.connect(self.localMysqlIP, self.localMysqlUser, self.localMysqlPass, "shotmachine")
            cursor = db.cursor(pymysql.cursors.Cursor)
            cursor.execute(sql_check_username.format(barcode, self.party_id))
            result = cursor.fetchone()
            cursor.close()
            db.close()

            if result == None:
                self.logger.info("No user found with barcode: " + str(barcode))
                return ""
            else:
                Username = result[0]
                self.logger.info("User found with barcode: " + str(barcode) + " User: " + str(Username))
                return str(Username)
        except:
            self.logger.warning("Unexpected error:", sys.exc_info()[0])
            try:
                db.rollback()
                db.close()
            except:
                pass
            return ""


    def ShotToDatabase(self, barcode, shot):
        sql_get_shot_id = "SELECT shot_id FROM party_has_shots WHERE(party_id={} AND tank_index = {});"
        sql_get_user_id = "SELECT id FROM users WHERE (barcode = {} AND party_id = {});"
        sql_get_organiser_barcode = "SELECT barcode FROM users WHERE party_id = {};"
        sql_write_shot = "INSERT INTO takenshots (datetime, shot_id, user_id, party_id, created_at, updated_at) VALUES (now(), %s, %s, %s,  now(), now());"
        try:
            db = pymysql.connect(self.localMysqlIP, self.localMysqlUser, self.localMysqlPass, "shotmachine")
            cursor = db.cursor(pymysql.cursors.Cursor)
            cursor.execute(sql_get_shot_id.format(self.party_id, shot))
            shot_id = str(cursor.fetchone()[0])
            if barcode == "":
                cursor.execute(sql_get_organiser_barcode.format(self.party_id))
                barcode = str(cursor.fetchone()[0])
                self.logger.info("No barcode scanned, using organizer barcode: " + barcode)
            cursor.execute(sql_get_user_id.format(barcode, self.party_id))
            user_id = str(cursor.fetchone()[0])
            cursor.execute(sql_write_shot, (shot_id, user_id, str(self.party_id)))
            db.commit()
            cursor.close()
            db.close()
        except:
            self.logger.warning("Unexpected error:", sys.exc_info()[0])
            try:
                db.rollback()
                db.close()
            except:
                pass


    def getLastSyncTime(self):
        try:
            sql_get_last_sync = "SELECT last_sync FROM machines WHERE id = {};"
            db = pymysql.connect(self.localMysqlIP, self.localMysqlUser, self.localMysqlPass, "shotmachine")

            cursor = db.cursor(pymysql.cursors.Cursor)
            cursor.execute(sql_get_last_sync.format('1'))
            answer = cursor.fetchone()
            sync_time = str(answer[0])
            cursor.close()
            db.close()
            return sync_time
        except:
            print("Unexpected error:", sys.exc_info()[0])
            try:
                db.rollback()
                db.close()
            except:
                pass
            return "Error"

    #def pictureToDatabase(self):

    def GetGoogleAlbumId(self, partyId):            ### Old uploader, can probably be removed
        sql_get_google_album_id = "SELECT google_photoalbum_id FROM parties WHERE id={};"
        db = pymysql.connect(self.localMysqlIP, self.localMysqlUser, self.localMysqlPass, "shotmachine")

        cursor = db.cursor(pymysql.cursors.Cursor)
        cursor.execute(sql_get_google_album_id.format(str(partyId)))
        answer = cursor.fetchone()
        albumId = str(answer[0])
        cursor.close()
        db.close()
        return albumId

    def SetGoogleAlbumId(self, partyID, Album_Id, albumurl):     ### Old uploader, can probably be removed
        sql_write_Google_album_data = "INSERT INTO parties (google_photoalbum_id, google_photoshareable_url) VALUES (%s, %s) WHERE id=%s;"
        try:
            db = pymysql.connect(self.localMysqlIP, self.localMysqlUser, self.localMysqlPass, "shotmachine")
            cursor.execute(sql_write_Google_album_data, (Album_Id, albumurl, partyID))
            db.commit()
            cursor.close()
            db.close()
        except:
            self.logger.warning("Unexpected error:", sys.exc_info()[0])
            try:
                db.rollback()
                db.close()
            except:
                pass

    def SetPhotoToUser(self, party_id, barcode, imagename, timestamp):
        self.logger.info("start writing photo to db")
        sql_get_user_id = "SELECT id FROM users WHERE (barcode = {} AND party_id = {});"
        sql_get_organiser_barcode = "SELECT barcode FROM users WHERE party_id = {};"
        sql_write_picture = "INSERT INTO photos (datetime, user_id, party_id, picture_name, created_at ,updated_at) VALUES (%s, %s, %s, %s, %s, %s);"
        try:
            db = pymysql.connect(self.onlineMysqlIP, self.onlineMysqlUser, self.onlineMysqlPass, "shotmachine")
            cursor = db.cursor(pymysql.cursors.Cursor)
            if barcode == "":
                cursor.execute(sql_get_organiser_barcode.format(self.party_id))
                barcode = str(cursor.fetchone()[0])
                self.logger.info("No barcode scanned, using organizer barcode: " + barcode)
            cursor.execute(sql_get_user_id.format(barcode, party_id))
            user_id = str(cursor.fetchone()[0])
            self.logger.info("User_id: " + user_id)
            cursor.execute(sql_write_picture, (timestamp, user_id, party_id, imagename, timestamp, timestamp))
            db.commit()
            cursor.close()
            db.close()
            self.logger.info("finished writing to db")
        except:
            self.logger.warning("Unexpected error:", sys.exc_info()[0])
            try:
                db.rollback()
                db.close()
            except:
                pass

