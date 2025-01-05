import sys
import os
#from google_auth_oauthlib.flow import InstalledAppFlow
#from googleapiclient.discovery import build
#dir(sys)
#sys.path.append('C:/Users/marce/Dropbox/Drank-O-Matic/Software/Python/shotmachine2019/Functions/GooglePhotos')

import glob
from Functions.PhotoUploader.google_photos_functions import googlePhotoUploader

### Variables ###


#Album_Id = 'AOivGk9mA_hdf1F75tg5n3GxCN_BHFHY-Z2-rnWZXQTLFRoeq6FpMBfyatxwjfFOiWDnNxPfLF_5'
#Album_Id = 'AF1QipMFoLy5iM7PedDWDyhatNjgsGf4YaGzEz6i_nJxugPSlrW85tRnw4_HbphJaWo72g'
Album_Id = 'AOivGk-LGHTCvhw6L5NcOSpFbLYez9wafktpnpUQ0av4uqQxm4Yme-hTLCblvVchNOdAKgRikfHh'
#album_name = 'uploaded fotos'
album_name = 'Uploaded'

Create_new_album = True

createAlbum = True

### Main code ###

googlePhotoHandle = googlePhotoUploader(Album_Id)
#(albumurl, Album_Id) = googlePhotoHandle.create_album("Uploaded")
#googlePhotoHandle.list_albums()
response = googlePhotoHandle.uploadPicture('./TakenImages/NotUploaded/20250102_204137.jpg', '20250102_204137.jpg')
'''
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
'''
