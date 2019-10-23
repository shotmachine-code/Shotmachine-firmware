import threading
import sys
import os
import queue
import glob
import time
import datetime
from Functions.GooglePhotos.google_photos_functions import googlePhotoUploader
from Functions.Database import database_connection
import logging
import pysftp
import xml.etree.ElementTree as ET

#logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)

#Album_Id = 'AOivGk9mA_hdf1F75tg5n3GxCN_BHFHY-Z2-rnWZXQTLFRoeq6FpMBfyatxwjfFOiWDnNxPfLF_5'
#album_name = 'Housewarming Lisa 2'
#Create_new_album = False

class PhotoUploader():
    def __init__(self, _partyid, _ToPhotoUploaderQueue):

        self.ToDoQueue = _ToPhotoUploaderQueue
        self.party_id = str(_partyid)

        self.db_conn = database_connection.database_connection()
        done = False
        self.logger = logging.getLogger(__name__)

        GooglePhotoUploader = False
        sftpUploader = True

        if GooglePhotoUploader:
            while not done:
                try:
                    self.logger.info("Start Google photo uploader")

                    self.AlbumId = self.db_conn.GetGoogleAlbumId(self.party_id)
                    self.logger.info("Google photo uploader album ID: " + self.AlbumId)

                    if self.AlbumId == None:
                        self.logger.info("No album ID known, create new album")
                        (albumurl, self.AlbumId) = googlePhotoHandle.create_album(album_name)
                        self.db_conn.SetGoogleAlbumId(self.party_id, self.AlbumId, albumurl)
                    self.googlePhotoHandle = googlePhotoUploader(self.AlbumId)

                    self.run = True
                    self.thread = threading.Thread(target=self.uploaderThreadGoogle)
                    self.thread.start()
                    done = True
                    self.logger.info("Google photo uploader succesfully started")
                except:
                    self.logger.warning("Error in starting google photo uploader, try again")


        if sftpUploader:
            self.logger.info("start SFTP uploader")
            self.sftpUser = ""
            self.sftpPass = ""
            self.sftpAdress = ""

            try:
                xml_file_path = os.path.join(os.getcwd(), 'settings.xml')
                tree = ET.parse(xml_file_path)
                root = tree.getroot()
                for settingsXML in root.findall('sftp'):
                    if settingsXML.get('name') == 'sftp_server':
                        self.sftpUser = settingsXML.find('user').text
                        self.sftpPass = settingsXML.find('password').text
                        self.sftpAdress = settingsXML.find('adress').text
                        self.sftpHostKey = settingsXML.find('hostkey').text
            except:
                self.logger.error("error in loading settings from xml file")
                raise

            #cnopts = CnOpts()

            #hostkeys = None

            #if cnopts.hostkeys.lookup(host) == None:
                #print("New host - will accept any host key")
                # Backup loaded .ssh/known_hosts file
                #hostkeys = cnopts.hostkeys
                # And do not verify host key of the new host
                #cnopts.hostkeys = None

            #with Connection(host, username=user, private_key=pkey, cnopts=cnopts) as sftp:
            #    if hostkeys != None:
            #        print("Connected to new host, caching its hostkey")
            #        hostkeys.add(host, sftp.remote_server_key.get_name(), sftp.remote_server_key)
            #        hostkeys.save(pysftp.helpers.known_hosts())
            cnopts = pysftp.CnOpts()
            #cnopts.hostkeys.load('')

            try:
                with pysftp.Connection(host=self.sftpAdress, username=self.sftpUser, password=self.sftpPass, cnopts=cnopts) as sftp:
                    #if hostkeys != None:
                    #    print("Connected to new host, caching its hostkey")
                    #    hostkeys.add(host, sftp.remote_server_key.get_name(), sftp.remote_server_key)
                    #    hostkeys.save(pysftp.helpers.known_hosts())
                    self.logger.info("Connection succesfully stablished with sftp server")
                    remoteFilePath = '/root/Photos/' + self.party_id + '/'
                    DirExists = sftp.exists(remoteFilePath)
                    if not DirExists:
                        self.logger.info("Directory is not existing on sftp server, create it")
                        sftp.mkdir(remoteFilePath)
            except:
                self.logger.error("Could not cheack/create directory on remote sftp server")
                raise

            self.run = True
            self.thread = threading.Thread(target=self.uploaderThreadSFTP)
            self.thread.start()



    def uploaderThreadSFTP(self):
        self.logger.info("SFTP photo uploader started")
        while self.run:
            try:
                Task = self.ToDoQueue.get(block=True, timeout=1)

                if Task == "Quit":
                    self.run = False
                elif Task != "":
                    self.logger.info("New photo to upload: " + Task)
                    ts = time.time()
                    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    Filename = Task.split(':')[0]
                    print("Filename: " + Filename)
                    Barcode = Task.split(':')[1]
                    print("Barcode: " + Barcode)
                    photoname = Filename.split('/')[-1]
                    print('photoname: ' + photoname)
                    time.sleep(5)
                    try:
                        with pysftp.Connection(host=self.sftpAdress, username=self.sftpUser, password=self.sftpPass) as sftp:
                            self.logger.info("Connection succesfully stablished with sftp server")
                            remoteFilePath = '/root/Photos/'+ self.party_id + '/' + photoname
                            sftp.put(Filename, remoteFilePath)
                    except:
                        self.logger.warning("Upload failed, try again")
                        self.ToDoQueue.put(Filename + ":" + Barcode)

                    self.logger.info("upload success")
                    self.db_conn.SetPhotoToUser(self.party_id, Barcode, photoname, timestamp)
                    self.logger.info("photo written to db")


            except queue.Empty:
                continue
        self.logger.info("Uploader thread closed")

            


    def uploaderThreadGoogle(self):
        print("6")
        while self.run:
            try:
                print("7")
                Task = self.ToDoQueue.get(block=True, timeout=1)
                print("8")
                print(Task)
                if Task == "Quit":
                    self.run = False
                elif Task != "":
                    print("9")
                    ts = time.time()
                    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    Filename = Task.split(':')[0]
                    print("Filename: " + Filename)
                    Barcode = Task.split(':')[1]
                    print("Barcode: " + Barcode)
                    photoname = Filename.split('/')[-1]
                    print('photoname: ' + photoname)
                    time.sleep(5)
                    response = self.googlePhotoHandle.uploadPicture(Filename, photoname)
                    print("10")
                    if not response:
                        print("upload failed")
                        self.ToDoQueue.put(Filename + ":" + Barcode)
                    print("upload success")
                    self.db_conn.SetPhotoToUser(self.party_id, Barcode, Filename, timestamp)
                    print("photo written to db")


            except queue.Empty:
                continue
