import threading
import sys
import os
import queue
import glob
import time
import datetime
#from Functions.GooglePhotos.google_photos_functions import googlePhotoUploader
from Functions.PhotoUploader.google_photos_functions import googlePhotoUploader
from Functions.Database import database_connection
import logging
import pysftp
import xml.etree.ElementTree as ET
import shutil


Album_Id = 'AOivGk-LGHTCvhw6L5NcOSpFbLYez9wafktpnpUQ0av4uqQxm4Yme-hTLCblvVchNOdAKgRikfHh'
album_name = 'Uploaded'
#Album_Id = None

#Create_new_album = False

class photo_uploader():
    def __init__(self, _ToPhotoUploaderQueue, _HandleShotmachine):

        self.ToDoQueue = _ToPhotoUploaderQueue
        self.HandleShotmachine = _HandleShotmachine

        self.party_id = str(self.HandleShotmachine["Settings"]["PartyId"])
        self.InternetConnection = str(self.HandleShotmachine["Settings"]["InternetConnection"])
        
        self.logger = logging.getLogger(__name__)
        self.db_conn = database_connection.database_connection(self.HandleShotmachine)
        
        MainUploadedFolder = 'TakenImages/Uploaded'
        if not (os.path.isdir(MainUploadedFolder)):
            os.mkdir(MainUploadedFolder)
            self.logger.info("Created main folder for uploaded images: " + MainUploadedFolder)
        
        #self.UploadedFolder = MainUploadedFolder + "/"+ self.party_id
        self.UploadedFolder = MainUploadedFolder
        if not (os.path.isdir(self.UploadedFolder)):
            os.mkdir(self.UploadedFolder)
            self.logger.info("Created folder for uploaded images of this party: " + self.UploadedFolder)
        
        done = False
        
        if self.InternetConnection == "True":
            GooglePhotoUploader = True         
            sftpUploader = False
            self.logger.info("Internet connection working, start uploader")
        else:
            GooglePhotoUploader = False         
            sftpUploader = False
            self.logger.info("No internet connection working, do not start uploader")

        if GooglePhotoUploader:     ### Old uploader, can probably be removed
            #while not done:
            #try:
                self.logger.info("Start Google photo uploader")
                self.AlbumId = Album_Id
                #self.AlbumId = self.db_conn.GetGoogleAlbumId(self.party_id)
                #self.logger.info("Google photo uploader album ID: " + self.AlbumId)
                self.googlePhotoHandle = googlePhotoUploader(self.AlbumId)
                if self.AlbumId == None:
                    self.logger.info("No album ID known, create new album")
                    
                    #(albumurl, self.AlbumId) = googlePhotoUploader.create_album("Uploaded")
                    (albumurl, self.AlbumId) = self.googlePhotoHandle.create_album(album_name)
                    #self.db_conn.SetGoogleAlbumId(self.party_id, self.AlbumId, albumurl)
                self.logger.info("Google photo uploader album ID: " + self.AlbumId)
                #self.googlePhotoHandle = googlePhotoUploader(self.AlbumId)

                self.run = True
                self.thread = threading.Thread(target=self.uploaderThreadGoogle)
                self.thread.start()
                done = True
                self.logger.info("Google photo uploader succesfully started")
            #except:
                #self.logger.warning("Error in starting google photo uploader, try again")


        if sftpUploader:
            self.logger.info("start SFTP uploader")
            self.sftpUser = ""
            self.sftpPass = ""
            self.sftpAdress = ""

            cnopts = pysftp.CnOpts()

            try:
                xml_file_path = os.path.join(os.getcwd(), 'settings.xml')
                tree = ET.parse(xml_file_path)
                root = tree.getroot()
                for settingsXML in root.findall('sftp'):
                    if settingsXML.get('name') == 'sftp_server':
                        self.sftpUser = settingsXML.find('user').text
                        self.sftpPass = settingsXML.find('password').text
                        self.sftpAdress = settingsXML.find('adress').text
            except:
                self.logger.error("error in loading settings from xml file")
                raise

            try:
                with pysftp.Connection(host=self.sftpAdress, username=self.sftpUser, password=self.sftpPass, cnopts=cnopts) as sftp:
                    self.logger.info("Connection succesfully stablished with sftp server")
                    remoteFilePath = '/root/Photos/' + self.party_id + '/'
                    DirExists = sftp.exists(remoteFilePath)
                    if not DirExists:
                        self.logger.info("Directory is not existing on sftp server, create it")
                        sftp.mkdir(remoteFilePath)
                self.run = True
                self.thread = threading.Thread(target=self.uploaderThreadSFTP)
                self.thread.start()
            except ConnectionException as e:
                self.logger.error("No connection to sftp server, photo uploader not started")
            except:
                self.logger.error("Could not check/create directory on remote sftp server")
                raise
                

            #self.run = True
            #self.thread = threading.Thread(target=self.uploaderThreadSFTP)
            #self.thread.start()


    def uploaderThreadSFTP(self):
        self.logger.info("SFTP photo uploader started")
        while self.run:
            try:
                Task = self.ToDoQueue.get(block=True, timeout=1)
                if Task == "Quit":
                    self.run = False
                elif Task != "":
                    ts = time.time()
                    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    Filename = Task.split(':')[0]
                    Barcode = Task.split(':')[1]
                    photoname = Filename.split('/')[-1]
                    self.logger.info("New photo to upload: " + photoname + " For barcode: " + Barcode)
                    time.sleep(5)
                    try:
                        with pysftp.Connection(host=self.sftpAdress, username=self.sftpUser, password=self.sftpPass) as sftp:
                            self.logger.info("Connection succesfully stablished with sftp server")
                            remoteFilePath = '/root/Photos/'+ self.party_id + '/' + photoname
                            sftp.put(Filename, remoteFilePath)
                            self.logger.info("upload success")
                            self.db_conn.SetPhotoToUser(Barcode, photoname, timestamp)
                            self.logger.info("photo written to db")
                            shutil.move(Filename, (self.UploadedFolder + "/" + photoname))
                            self.logger.info("photo moved to uploaded folder under: " + (self.UploadedFolder + "/" + photoname))
                    except FileNotFoundError as e:
                        self.logger.warning("Upload failed, try again")
                        self.logger.warning(e)
                        self.ToDoQueue.put(Filename + ":" + Barcode)
            except queue.Empty:
                continue
        self.logger.info("Uploader thread closed")


    
    def uploaderThreadGoogle(self):
        #print("6")
        while self.run:
            try:
                #print("7")
                Task = self.ToDoQueue.get(block=True, timeout=1)
                #print(Task)
            except queue.Empty:
                #continue
                Task = ""
                pass
            filelist = glob.glob("/home/pi/Shotmachine/Shotmachine-firmware/TakenImages/NotUploaded/*.jpg")
            #print(filelist)
            #print("8")
            #print(Task)
            if Task == "Quit":
                self.run = False
            #elif Task != "":
            if len(filelist) > 0:
                self.logger.info('Start with uploading')
                    
                Filename = filelist[0].split('firmware/')[1]
                photoname = filelist[0].split('/')[-1]
                
                self.logger.info('Start uploading: ' + photoname)
                    
                #ts = time.time()
                #timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                #Filename = Task.split(':')[0]
                #print("Filename: " + Filename)
                #Barcode = Task.split(':')[1]
                #print("Barcode: " + Barcode)
                #photoname = Filename.split('/')[-1]
                #print('photoname: ' + photoname)
                time.sleep(5)
                response = self.googlePhotoHandle.uploadPicture(Filename, photoname)
                #print("10")
                if not response:
                    self.logger.info("Upload failed")
                    self.ToDoQueue.put(Filename + ":" + Barcode)
                else:
                    self.logger.info("Upload success")
                    #self.db_conn.SetPhotoToUser(self.party_id, Barcode, Filename, timestamp)
                    #print("photo written to db")
                    shutil.move(Filename, (self.UploadedFolder + "/" + photoname))
                    self.logger.info("Photo moved to uploaded folder under: " + (self.UploadedFolder + "/" + photoname))

            
