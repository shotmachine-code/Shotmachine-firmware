import pymysql
import sys
from threading import Thread
import logging
import queue

################

class DatabaseSync:
    def __init__(self, _queue):

        self.fromMainQueue = _queue



        self.sql = "UPDATE machines SET last_sync = NOW() WHERE machine_name = 'Prototype 1'"

        self.run = True
        self.recievebuffer = ''
        self.logger = logging.getLogger("Foto_Uploader")

        self.mainThread = Thread(target=self.main_db_syncer, name='dbsync_main')
        self.mainThread.start()
        self.queueThread = Thread(target=self.queue_watcher, name='dbSync_watcher')
        self.queueThread.start()

        self.logger.info('Database syncer started')

    def queue_watcher(self):
        self.run = True
        while self.run:
            if self.recievebuffer == '':
                try:
                    self.recievebuffer = self.fromMainQueue.get(block=True, timeout=0.1)
                    print(self.recievebuffer)
                    if self.recievebuffer == "Quit":
                        self.run = False
                except queue.Empty:
                    continue
            time.sleep(0.1)

    def main_db_syncer(self):

        while self.run:
            try:
                self.db = pymysql.connect("localhost", "root", "Aardslappel987", "shotmachine")
                self.cursor = self.db.cursor()
                self.cursor.execute("SELECT VERSION()")
                dbVersion = self.cursor.fetchone()
                self.logger.info("Connected to local database with version : %s " % dbVersion)

                # full sync from online to local
                self.logger.info("Perform full sync from online DB to local DB")
                answer = os.popen(self.FullSyncFromOnline).read()
                print(answer)
                while self.run:
                    try:
                        self.cursor.execute(self.sql)
                        self.db.commit()
                    except:
                        self.logger.info("Unexpected error:", sys.exc_info()[0])
                        self.db.rollback()
                        self.logger.info("Error in sql")
                    # update sync to online database since last sync
                    curr_time = datetime.datetime.now().strftime("%Y-%m-%m %H:%M:%S")
                    self.logger.info("Perform update sync from local DB to online DB")
                    #print(curr_time)
                    answer = os.popen(self.LastSyncToOnline).read()
                    print(answer)
                    print("Perform update sync from online DB to local DB")
                    answer = os.popen(self.LastSyncFromOnline.format(self.party_id)).read()
                    print(answer)
                    print("Sync last synctime to online DB")
                    answer = os.popen(self.LastSyncTimeToOnline.format(self.machine_id)).read()
                    print(answer)
                    time.sleep(1)

            finally:
                self.db.close()
                print("Closed program")
