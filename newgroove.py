#!/usr/bin/python

import requests
import random
import string
import uuid
import hashlib
import json


class Shark:

    def __init__(self):
        self.base_url = 'https://grooveshark.com'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36'}
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.token = ''
        country = {'CC1': 72057594037927940,
                   'CC2': 0,
                   'CC3': 0,
                   'CC4': 0,
                   'ID': 57,
                   'IPR': 0}
        self.payload_header = {'country': country,
                               'privacy': 0,
                               'session': self.__makeSessionId(),
                               'uuid': str.upper(str(uuid.uuid4())),
                               'clientRevision': '20130520'}
        self.getToken()

    def __makeSessionId(self):
        """Just pick 32 characters from digits or letters randomly."""
        return (''.join(random.choice(string.digits + string.letters[:6]) for i in range(32)).lower())

    def __makeToken(self, method):
        texts = (''.join([random.choice(string.digits + string.letters[:6])
                 for i in range(6)])).lower()
        return texts + hashlib.sha1('%s:%s:%s:%s' % (method, self.token, 'nuggetsOfBaller', texts)).hexdigest()

    def __makeQueueId(self):
        return random.randint(10000000000000000000000, 99999999999999999999999)

    def getToken(self):
        method = 'getCommunicationToken'

        header = {'client': 'htmlshark'}
        header.update(self.payload_header)
        data = {
            'parameters': {'secretKey': hashlib.md5(header['session']).hexdigest()},
            'method': method,
            'header': header}
        response = self.session.post(
            self.base_url + '/more.php', data=json.dumps(data))
        if response.status_code == 200:
            self.token = response.json()['result']

    def searchSong(self, query):
        method = 'getResultsFromSearch'

        header = {'token': self.__makeToken(method),
                  'client': 'htmlshark'}
        header.update(self.payload_header)
        data = {
            'parameters': {'type': 'Songs',
                           'query': query},
            'header': header,
            'method': method}
        response = self.session.post(self.base_url + '/more.php?' + method,
                                     data=json.dumps(data))
        return response.json()['result']['result']

    def downloadSongs(self, songs):
        queue_id = self.__makeQueueId()
        for song in songs:
            self.addSongsToQueue(song, queue_id)
            stream = self.getStreamKeyFromSongIDs(song['SongID'])
            self.downloadSong(stream, song)
            self.markSongDownloadedEx(stream, song)

    def addSongsToQueue(self, song, queue_id):
        """Add a song to the browser queue, used to imitate a browser."""

        method = 'addSongsToQueue'
        parameters = {'songQueueID': queue_id,
                      'songIDsArtistIDs': [{'songID': song['SongID'],
                                           'artistID': song['ArtistID'],
                                            'source': 'user',
                                            'songQueueSongID': 1}]}
        header = {'token': self.__makeToken(method),
                  'client': 'jsqueue'}
        header.update(self.payload_header)
        data = {'header': header,
                'parameters': parameters,
                'method': method}
        self.session.post(
            self.base_url + '/more.php?' + method, data=json.dumps(data))

    def getStreamKeyFromSongIDs(self, id):
        method = 'getStreamKeysFromSongIDs'
        header = {'token': self.__makeToken(method),
                  'client': 'jsqueue'}
        header.update(self.payload_header)
        parameters = {'type': '8',
                      'mobile': False,
                      'prefetch': False,
                      'songIDs': id,
                      'country': header['country']}
        data = {'header': header,
                'parameters': parameters,
                'method': method}
        response = self.session.post(
            self.base_url + '/more.php?' + method, data=json.dumps(data))
        return response.json()['result'][id]

    def markSongDownloadedEx(self, stream, song):
        method = 'markSongDownloadedEx'
        header = {'token': self.__makeToken(method),
                  'client': 'jsqueue'}
        header.update(self.payload_header)
        parameters = {'streamServerID': stream['ip'],
                      'streamKey': stream['streamKey'],
                      'songID': song['SongID']}
        data = {'header': header,
                'parameters': parameters,
                'method': method}
        self.session.post(self.base_url + '/more.php?' + method,
                          data=json.dumps(data))

    def downloadSong(self, stream, song):
        file_name = '%s - %s.mp3' % (song['SongName'], song['ArtistName'])
        url = 'http://%s/stream.php' % (stream['ip'])

        print 'Download %s - %s' % (song['SongName'], song['ArtistName']) 

        data = {'streamKey': stream['streamKey']}
        response = self.session.post(url, data=data, stream=True)
        with open(file_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()


def main():
    shark = Shark()
    songs = shark.searchSong('query')

if __name__ == '__main__':
    main()
