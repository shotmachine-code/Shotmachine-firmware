import sys
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
dir(sys)
#sys.path.append('C:/Users/marce/Dropbox/Drank-O-Matic/Software/Python/shotmachine2019/Functions/GooglePhotos')

import glob
from Functions.GooglePhotos.google_photos_functions import *

### Variables ###

scopes = ['https://www.googleapis.com/auth/photoslibrary', 'https://www.googleapis.com/auth/photoslibrary.sharing']
Album_Id = 'AOivGk9mA_hdf1F75tg5n3GxCN_BHFHY-Z2-rnWZXQTLFRoeq6FpMBfyatxwjfFOiWDnNxPfLF_5'
album_name = 'Housewarming Lisa'
Create_new_album = False

### Main code ###

if __name__ == "__main__":
    # get credentials from file in case the access is granted before
    [creds, result] = Get_Credentials()

    # No valid credentials have been found, ask user for new one
    if not result:
        print('No credentials found, requesting from user')
        clientID_file = './Functions/GooglePhotos_final/client_id.json'
        flow = InstalledAppFlow.from_client_secrets_file(clientID_file, scopes)
        creds = flow.run_local_server(host='localhost',
                                  port=8090,
                                  authorization_prompt_message='Please visit this URL: {url}',
                                  success_message='The authentication is complete; you may close this window.',
                                  open_browser=True)
        Save_Credentials(creds)

    # Build handler and refresh access token
    service = build('photoslibrary', 'v1', credentials = creds)
    results = service.albums().list(pageSize=10).execute()

    # Create new album example
    if Create_new_album == True:
        [Album_Id, albumURL] = create_album(creds, album_name)

    filelist = glob.glob("./TakenImages/NotUploaded/*.png")
    print(filelist)
    for foto in filelist:
        print("Uploading file " + foto)
        foto.split('/')[3]
        fotoname = "Housewarming Lisa " + foto.split('/')[3]
        # Upload picture to album (2 steps required)
        response = uploadPicture(creds, foto, Album_Id, fotoname)
        #response = createItem(creds,upload_token, Album_Id, foto)
        print(response)
