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

logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)

#Album_Id = 'AOivGk9mA_hdf1F75tg5n3GxCN_BHFHY-Z2-rnWZXQTLFRoeq6FpMBfyatxwjfFOiWDnNxPfLF_5'
#album_name = 'Housewarming Lisa 2'
#Create_new_album = False

class PhotoUploader():
    def __init__(self, _partyid, _ToPhotoUploaderQueue):
        done = False
        while not done:
            try:
                logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)
                print("Start upoader")
                self.ToDoQueue = _ToPhotoUploaderQueue
                self.party_id = _partyid
                self.db_conn = database_connection.database_connection()
                print("1")
                self.AlbumId = self.db_conn.GetGoogleAlbumId(self.party_id)
                print("2")
                print(self.AlbumId)
                if self.AlbumId == None:
                    print("3")
                    (albumurl, self.AlbumId) = googlePhotoHandle.create_album(album_name)
                    self.db_conn.SetGoogleAlbumId(self.party_id, self.AlbumId, albumurl)
                    print("4")

                self.googlePhotoHandle = googlePhotoUploader(self.AlbumId)
                print("5")
                #self.ToDoQueue = queue.Queue()
                self.run = True

                self.thread = threading.Thread(target=self.uploaderThread)
                self.thread.start()
                done = True
            except:
                continue
            


    def uploaderThread(self):
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


    #def UploadImage(self, Filename, Barcode):
    #    self.ToDoQueue.put(Filename + ":" + Barcode)

    #def StopUploader(self):
    #    self.run = False


### Main code ###

#googlePhotoHandle = googlePhotoUploader(Album_Id)

#if createAlbum:
#    (albumurl, Album_Id) = googlePhotoHandle.create_album(album_name)
#    print(albumurl)
#    print(Album_Id)

#filelist = glob.glob("./TakenImages/NotUploaded/*")
#print(filelist)
#for foto in filelist:
#    print("Uploading file " + foto)
#    foto.split('/')[3]
#    fotoname = "Housewarming Lisa " + foto.split('/')[3]
#    response = googlePhotoHandle.uploadPicture(foto, fotoname)
#    print(response)
