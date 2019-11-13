import os
import datetime
import time
import pymysql
import sys
from threading import Thread
import logging
import queue
import xml.etree.ElementTree as ET

################

class DatabaseSync:
    def __init__(self, _tosyncqueue, _tomainqueue, _HandleShotmachine):
        try:
            # read input variables
            self.fromMainQueue = _tosyncqueue
            self.toMainQueue = _tomainqueue
            self.HandleShotmachine = _HandleShotmachine

            # start logger
            self.logger = logging.getLogger("Database_sync")

            # Get mysql settings from settings file
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

            # Prepare mysql commands
            self.FullSyncFromOnline =    'pt-table-sync --execute --verbose ' + \
                                    '-t error_logs,error_types,machines,parties,party_has_shots,photos,shots,takenshots,users ' + \
                                    'h=' + self.onlineMysqlIP + ', -u ' + self.onlineMysqlUser +', -p' + self.onlineMysqlPass + \
                                    ', h=' + self.localMysqlIP + ', -u ' + self.localMysqlUser + ', -p' + self.localMysqlPass
            self.LastSyncToOnline = 'pt-table-sync --execute --verbose --set-vars wait_timeout=60 --where "created_at > CURDATE() - INTERVAL 1 DAY" ' + \
                               '-t takenshots,error_logs ' + \
                               'h=' + self.localMysqlIP + ', -u ' + self.localMysqlUser + ', -p' + self.localMysqlPass + \
                               ', h=' + self.onlineMysqlIP + ', -u ' + self.onlineMysqlUser +', -p' + self.onlineMysqlPass
            self.LastSyncTimeToOnline = 'pt-table-sync --execute --verbose --set-vars wait_timeout=60 --where "id = {}" ' + \
                                   '-t machines ' + \
                                   'h=' + self.localMysqlIP + ', -u ' + self.localMysqlUser + ', -p' + self.localMysqlPass + \
                                   ', h=' + self.onlineMysqlIP + ', -u ' + self.onlineMysqlUser +', -p' + self.onlineMysqlPass
            self.LastSyncFromOnline = 'pt-table-sync --execute --verbose --set-vars wait_timeout=60 --where "party_id = {}" ' + \
                                 '-t users ' + \
                                 'h=' + self.onlineMysqlIP + ', -u ' + self.onlineMysqlUser +', -p' + self.onlineMysqlPass + \
                                 ', h=' + self.localMysqlIP + ', -u ' + self.localMysqlUser + ', -p' + self.localMysqlPass
            self.UpdateLastSyncTime = "UPDATE machines SET last_sync = NOW() WHERE machine_name = 'Prototype 1'"

            # extract essential settings from setting struct
            self.machine_id = self.HandleShotmachine["Settings"]["MachineId"]
            self.party_id = self.HandleShotmachine["Settings"]["PartyId"]

            # prepare variables needed to run treads
            self.run = True
            self.recievebuffer = ''

            # start threads
            self.mainThread = Thread(target=self.main_db_syncer, name='dbsync_main')
            self.mainThread.start()
            self.queueThread = Thread(target=self.queue_watcher, name='dbSync_watcher')
            self.queueThread.start()

            # wrap up init
            self.logger.info('Database syncer started')

        except:
            # error in starting the syncer
            self.logger.error('Error in starting database sync')
            raise

    def queue_watcher(self):
        self.run = True
        while self.run:
            if self.recievebuffer == '':
                try:
                    self.recievebuffer = self.fromMainQueue.get(block=True, timeout=0.1)
                    if self.recievebuffer == "Quit":
                        self.run = False
                        self.logger.info("DB sync quit")
                except queue.Empty:
                    continue
            time.sleep(0.1)

    def main_db_syncer(self):

        while self.run:
            try:
                self.db = pymysql.connect(self.localMysqlIP, self.localMysqlUser, self.localMysqlPass, "shotmachine")
                self.cursor = self.db.cursor()
                self.cursor.execute("SELECT VERSION()")
                dbVersion = self.cursor.fetchone()
                self.logger.info("Connected to local database with version : %s " % dbVersion)

                # full sync from online to local
                self.logger.info("Perform full sync from online DB to local DB")
                answer = os.popen(self.FullSyncFromOnline).read()
                #print(answer)

                while self.run:
                    # update time of update in db
                    try:
                        self.cursor.execute(self.UpdateLastSyncTime)
                        self.db.commit()
                    except:
                        self.logger.info("Unexpected error:", sys.exc_info()[0])
                        self.db.rollback()
                        self.logger.info("Error in sql")
                    
                    # sync from local to online
                    self.logger.info("Perform update sync from local DB to online DB")
                    answer = os.popen(self.LastSyncToOnline).read()
                    #print(answer)
                    if not self.run:
                        break
                        
                    # sync from online to local
                    self.logger.info("Perform update sync from online DB to local DB")
                    answer = os.popen(self.LastSyncFromOnline.format(self.party_id)).read()
                    #print(answer)
                    if not self.run:
                        break
                        
                    # update synctime in online db
                    self.logger.info("Sync last synctime to online DB")
                    answer = os.popen(self.LastSyncTimeToOnline.format(self.machine_id)).read()
                    #print(answer)
                    time.sleep(1)

            finally:
                self.db.close()
                self.logger.info("Closed db sync program")
