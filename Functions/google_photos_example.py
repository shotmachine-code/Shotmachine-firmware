import sys
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
#dir(sys)
#sys.path.append('C:/Users/marce/Dropbox/Drank-O-Matic/Software/Python/shotmachine2019/Functions/GooglePhotos')

from Functions.GooglePhotos.googlephotosupoader import GooglePhotosUploader

### Variables ###

#scopes = ['https://www.googleapis.com/auth/photoslibrary', 'https://www.googleapis.com/auth/photoslibrary.sharing']
Album_Id = 'AEMhHtqma5l8RSorkoRzzYtF-nbJu1AiU1hCkSO-8RfYMqYu_ZLmjoY'
album_name = 'Shotmachine testalbum'

Image_path = 'shot-glaasjes-van-anchor-hocking-3661u.png'
image_name = 'Test picture'
Create_new_album = True

### Main code ###

# initialize uploader
handler = GooglePhotosUploader()
# get credentials from file in case the access is granted before
    #[creds, result] = Get_Credentials()

    # No valid credentials have been found, ask user for new one
    #if not result:
    #    print('No credentials found, requesting from user')
    #    clientID_file = './GooglePhotos/client_id.json'
    #    flow = InstalledAppFlow.from_client_secrets_file(clientID_file, scopes)
    #    creds = flow.run_local_server(host='localhost',
    #                              port=8090,
    #                              authorization_prompt_message='Please visit this URL: {url}',
    #                              success_message='The authentication is complete; you may close this window.',
    #                              open_browser=True)
    #    Save_Credentials(creds)

    # Build handler and refresh access token
    #service = build('photoslibrary', 'v1', credentials = creds)
    #results = service.albums().list(pageSize=10).execute()

    # Create new album example
if Create_new_album == True:
    [Album_Id, albumURL] = handler.create_album(album_name)

    # Upload picture to album (2 steps required)
upload_token = handler.upload(Image_path, image_name, Album_Id)
    #response = createItem(creds,upload_token, Album_Id, )
