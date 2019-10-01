
import sys
import os
import glob
from Functions.GooglePhotos.google_photos_functions import googlePhotoUploader
import logging

logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)

#Album_Id = 'AOivGk9mA_hdf1F75tg5n3GxCN_BHFHY-Z2-rnWZXQTLFRoeq6FpMBfyatxwjfFOiWDnNxPfLF_5'
#album_name = 'Housewarming Lisa 2'
#Create_new_album = False

class PhotoUploader(_ToPhotoUploaderQueue):
    def __init__(self, _partyid):
        self.ToDoQueue = _ToPhotoUploaderQueue
        self.party_id = _partyid
        self.db_conn = database_connection.database_connection()
        self.AlbumId = self.db_conn.GetGoogleAlbumId(self.party_id)
        if self.AlbumId = None:
            (albumurl, Album_Id) = googlePhotoHandle.create_album(album_name)
            self.db_conn.SetGoogleAlbumId(self.party_id, Album_Id, albumurl)

        self.googlePhotoHandle = googlePhotoUploader(self.Album_Id)

        #self.ToDoQueue = queue.Queue()
        self.run = True

        self.thread = threading.Thread(target=self.uploaderThread, name=_name)
        self.thread.start()


    def uploaderThread(self):
        while self.run:
            try:
                Task = self.ToDoQueue.get(block=True, timeout=1)
                if Task == "Quit":
                    self.run = False
                if Task != ""
                    Filename = s.split(':')[0]
                    Barcode = s.split(':')[1]
                    photoname = foto.split('/')[3]
                    response = googlePhotoHandle.uploadPicture(Filename, photoname)
                    if not response:
                        print("upload failed")
                        self.ToDoQueue.put(Filename + ":" + Barcode)

                    self.db_conn.SetPhotoToUser(self.party_id, barcode, imagename)


            except:
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
