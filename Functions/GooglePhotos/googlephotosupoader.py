import json
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GooglePhotosUploader:
    def __init__(self):
        #self.credentials_file = 'Functions/GooglePhotos/credentials.json'
        self.credentials_file = 'GooglePhotos/credentials.json'
        #clientID_file = 'Functions/GooglePhotos/client_id.json'
        clientID_file = 'GooglePhotos/client_id.json'
        scopes = ['https://www.googleapis.com/auth/photoslibrary',
                  'https://www.googleapis.com/auth/photoslibrary.sharing']

        try:
            #credentials_file = './GooglePhotos/credentials.json'
            with open(self.credentials_file, 'r') as f:
                data = json.load(f)
            client_id = data[0]
            client_secret = data[1]
            id_token = data[2]
            refresh_token = data[3]
            scopes = data[4]
            token_uri = data[5]
            self.Creds = Credentials(None, refresh_token, id_token, token_uri, client_id, client_secret, scopes)
            #self.Creds.refresh
            service = build('photoslibrary', 'v1', credentials = self.Creds)
            results = service.albums().list(pageSize=10).execute()
            print('successfull retrieved credentials from file')
            #result = True
        except:
            print('No credentials found, requesting from user')
            # clientID_file = 'Functions/GooglePhotos/client_id.json'
            flow = InstalledAppFlow.from_client_secrets_file(clientID_file, scopes)
            self.Creds = flow.run_local_server(host='localhost',
                                          port=8090,
                                          authorization_prompt_message='Please visit this URL: {url}',
                                          success_message='The authentication is complete; you may close this window.',
                                          open_browser=True)
            self.Save_Credentials()


            #Creds = Credentials
            #print('failed to retrieved credentials from file')
            result = False

    def upload(self, file, picture_name, albumId):
        f = open(file, 'rb').read()
        url = 'https://photoslibrary.googleapis.com/v1/uploads'
        headers = {
            'Authorization': "Bearer " + self.Creds.token,
            'Content-Type': 'application/octet-stream',
            'X-Goog-Upload-File-Name': file,
            'X-Goog-Upload-Protocol': "raw",
        }
        r = requests.post(url, data=f, headers=headers)
        uploadtoken = str(r.content, 'utf-8')

        #def createItem(self, credentials, upload_token, albumId, picture_name):
        url = 'https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate'
        body = {
            'newMediaItems': [
                {
                    "description": picture_name,
                    "simpleMediaItem": {
                        "uploadToken": uploadtoken
                    }
                }
            ]
        }
        if albumId is not None:
            body['albumId'] = albumId
        bodySerialized = json.dumps(body)
        headers = {
            'Authorization': "Bearer " + self.Creds.token,
            'Content-Type': 'application/json',
        }
        response = requests.post(url, data=bodySerialized, headers=headers)
        jsn = ''.join(str(x, 'utf-8') for x in response.content.split())
        creation_info = json.loads(jsn)
        status = creation_info['newMediaItemResults'][0]['status']['message']
        if status == 'OK':
            result = True
            print('Succesfull uploaded ' + picture_name )
        else:
            result = False
            print('Failed to upload ' + picture_name )
        return result

    def create_album(self, album_name):
        url_create = 'https://photoslibrary.googleapis.com/v1/albums'
        headers = {
            'Authorization': "Bearer " + self.Creds.token,
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
        jsn = ''.join(str(x,'utf-8' ) for x in r.content.split())
        Album_info = json.loads(jsn)
        albumId = Album_info['id']

        url_share = 'https://photoslibrary.googleapis.com/v1/albums/' + albumId + ':share'
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
        albumUrl = share_info['shareInfo']['shareableUrl']
        print('New album created ')
        print('Name: ', albumTitle)
        print('ID: ', albumId)
        print('Sharable URL: ', albumUrl)
        return albumId, albumUrl

    def Save_Credentials(self,):
        #credentials_file = './GooglePhotos/credentials.json'
        credentials_data = []
        credentials_data.append(self.Creds.client_id)
        credentials_data.append(self.Creds.client_secret)
        credentials_data.append(self.Creds.id_token)
        credentials_data.append(self.Creds.refresh_token)
        credentials_data.append(self.Creds.scopes)
        credentials_data.append(self.Creds.token_uri)
        with open(self.credentials_file, 'w') as f:
            json.dump(credentials_data, f)
        print('Credentials saved')

