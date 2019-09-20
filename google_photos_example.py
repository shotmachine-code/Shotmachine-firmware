import sys
import os
#from google_auth_oauthlib.flow import InstalledAppFlow
#from googleapiclient.discovery import build
#dir(sys)
#sys.path.append('C:/Users/marce/Dropbox/Drank-O-Matic/Software/Python/shotmachine2019/Functions/GooglePhotos')

import glob
from Functions.GooglePhotos.google_photos_functions import googlePhotoUploader

### Variables ###


Album_Id = 'AOivGk9mA_hdf1F75tg5n3GxCN_BHFHY-Z2-rnWZXQTLFRoeq6FpMBfyatxwjfFOiWDnNxPfLF_5'
album_name = 'Housewarming Lisa 2'
Create_new_album = False

createAlbum = False

### Main code ###

googlePhotoHandle = googlePhotoUploader(Album_Id)

if createAlbum:
    (albumurl, Album_Id) = googlePhotoHandle.create_album(album_name)
    print(albumurl)
    print(Album_Id)

filelist = glob.glob("./TakenImages/NotUploaded/*")
print(filelist)
for foto in filelist:
    print("Uploading file " + foto)
    foto.split('/')[3]
    fotoname = "Housewarming Lisa " + foto.split('/')[3]
    response = googlePhotoHandle.uploadPicture(foto, fotoname)
    print(response)
