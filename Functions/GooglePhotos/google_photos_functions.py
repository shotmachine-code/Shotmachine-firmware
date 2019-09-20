import json
import requests
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

credentials_file = 'credentials.json'
clientID_file = 'client_id.json'

class googlePhotoUploader():
    def __init__(self, _albumId = None):
        scopes = ['https://www.googleapis.com/auth/photoslibrary',
                  'https://www.googleapis.com/auth/photoslibrary.sharing']
        print("start init uploader")
        result = self.Get_Credentials()
        #print(result)
        # No valid credentials have been found, ask user for new one
        if not result:
            print('No credentials found, requesting from user')
            clientID_file = './Functions/GooglePhotos_final/client_id.json'
            flow = InstalledAppFlow.from_client_secrets_file(clientID_file, scopes)
            self.credentials = flow.run_local_server(host='localhost',
                                          port=8090,
                                          authorization_prompt_message='Please visit this URL: {url}',
                                          success_message='The authentication is complete; you may close this window.',
                                          open_browser=True)
            self.Save_Credentials()

        # Build handler and refresh access token
        
        service = build('photoslibrary', 'v1', credentials=self.credentials, cache_discovery=False)
        results = service.albums().list(pageSize=10).execute()
        print("album id: " + _albumId)
        if _albumId == None:
            self.create_album()
        else:
            self.albumId = _albumId
        print("init uploader done")

    def Get_Credentials(self):
        try:
            credentials_file = './Functions/GooglePhotos_final/credentials.json'
            with open(credentials_file, 'r') as f:
                data = json.load(f)
            client_id = data[0]
            client_secret = data[1]
            id_token = data[2]
            refresh_token = data[3]
            scopes = data[4]
            token_uri = data[5]
            self.credentials = Credentials(None, refresh_token, id_token, token_uri, client_id, client_secret, scopes)
            self.credentials.refresh
            print('successfull retrieved credentials from file')
            result = True
        except:
            self.credentials = Credentials
            print('failed to retrieved credentials from file')
            result = False
        return result

    def Save_Credentials(self):
        credentials_file = './Functions/GooglePhotos_final/credentials.json'
        credentials_data = []
        credentials_data.append(self.credentials.client_id)
        credentials_data.append(self.credentials.client_secret)
        credentials_data.append(self.credentials.id_token)
        credentials_data.append(self.credentials.refresh_token)
        credentials_data.append(self.credentials.scopes)
        credentials_data.append(self.credentials.token_uri)
        with open(credentials_file, 'w') as f:
            json.dump(credentials_data, f)
        print('Credentials saved')

    def uploadPicture(self, _file, picture_name):
        print('21')
        f = open(_file, 'rb').read()
        url = 'https://photoslibrary.googleapis.com/v1/uploads'
        headers = {
            'Authorization': "Bearer " + self.credentials.token,
            'Content-Type': 'application/octet-stream',
            'X-Goog-Upload-File-Name': _file,
            'X-Goog-Upload-Protocol': "raw",
        }
        print('22')
        r = requests.post(url, data=f, headers=headers)
        print(r)
        upload_token = str(r.content, 'utf-8')
        print('23')
        url = 'https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate'
        body = {
            'newMediaItems': [
                {
                    "description": picture_name,
                    "simpleMediaItem": {
                        "uploadToken": upload_token
                    }
                }
            ]
        }
        print('23')
        if self.albumId is not None:
            body['albumId'] = self.albumId
        bodySerialized = json.dumps(body)
        headers = {
            'Authorization': "Bearer " + self.credentials.token,
            'Content-Type': 'application/json',
        }
        print('24')
        r = requests.post(url, data=bodySerialized, headers=headers)
        jsn = ''.join(str(x, 'utf-8') for x in r.content.split())
        creation_info = json.loads(jsn)
        status = creation_info['newMediaItemResults'][0]['status']['message']
        print('status: '+str(status))
        if status == 'Success':
            result = True
            print('Succesfull uploaded ' + picture_name)
        else:
            result = False
            print('Failed to upload ' + picture_name)
        return result

    def create_album(self, album_name):
        print('Create new album')
        url_create = 'https://photoslibrary.googleapis.com/v1/albums'
        headers = {
            'Authorization': "Bearer " + self.credentials.token,
            'Content-Type': 'application/json',
        }
        body_create = {
            "album":
                {
                    "title": album_name
                }
        }
        body_create_Serialized = json.dumps(body_create)
        r = requests.post(url_create, data=body_create_Serialized, headers=headers)
        jsn = ''.join(str(x, 'utf-8') for x in r.content.split())
        Album_info = json.loads(jsn)
        self.albumId = Album_info['id']

        url_share = 'https://photoslibrary.googleapis.com/v1/albums/' + self.albumId + ':share'
        body_share = {
            "sharedAlbumOptions": {
                "isCollaborative": False,
                "isCommentable": False
            }
        }
        body_share_Serialized = json.dumps(body_share)
        r = requests.post(url_share, data=body_share_Serialized, headers=headers)
        jsn = ''.join(str(x, 'utf-8') for x in r.content.split())
        share_info = json.loads(jsn)

        albumTitle = Album_info['title']
        self.albumurl = share_info['shareInfo']['shareableUrl']
        print('New album created ')
        print('Name: ', albumTitle)
        print('ID: ', self.albumId)
        print('Sharable URL: ', self.albumurl)
        return self.albumurl, self.albumId

    def getSharableURL(self):
        return self.albumurl







