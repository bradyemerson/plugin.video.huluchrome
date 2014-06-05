import xbmc
import xbmcgui
import xbmcplugin
import common
import sys
import binascii
import string
import base64
import os
import hmac
import operator
import time
import urllib
import re

from BeautifulSoup import BeautifulStoneSoup

import xml.etree.ElementTree as ElementTree


def log(txt, level=xbmc.LOGDEBUG):
       message = '%s: %s' % ("HULU : common.py :", txt)
       xbmc.log(msg=message, level=xbmc.LOGDEBUG)


smildeckeys = [ common.xmldeckeys[9] ]

class Main:

    def __init__( self ):

        if common.args.mode.endswith('TV_play'):
            if os.path.isfile(common.ADCACHE):
                os.remove(common.ADCACHE)
            self.GUID = common.makeGUID()
            
            if common.settings['enable_login']=='true' and common.settings['usertoken']:
                common.viewed(common.args.videoid) # POST VIEW
                
            video_id = common.args.url
            finalUrl = 'http://www.hulu.com/stand_alone/%s' % (str(video_id))
            smilSoup = self.getSMIL(video_id)
            displayname, infoLabels, segments = self.getMeta(smilSoup)
            item = xbmcgui.ListItem(displayname,path=finalUrl)
            item.setInfo( type="Video", infoLabels=infoLabels)
            item.setProperty('IsPlayable', 'true')
            xbmcplugin.setResolvedUrl(common.handle, True, item)
            
            if common.settings['queueremove']=='true' and common.settings['enable_login']=='true' and common.settings['usertoken']:
                self.queueViewComplete()
            

              
    def getSMIL(self, video_id,retry=0):
        epoch = int(time.mktime(time.gmtime()))
        parameters = {'video_id'  : video_id,
                      'v'         : '888324234',
                      'ts'        : str(epoch),
                      'np'        : '1',
                      'vp'        : '1',
                      'pc'        : '1', # added
                      'device_id' : self.GUID,
                      'pp'        : 'hulu', #added
                      'dp_id'     : 'hulu', #added
                      'region'    : 'US',
                      'ep'        : '1',
                      'language'  : 'en'
                      }


        if retry > 0:
            parameters['retry']=str(retry)
        if common.settings['enable_login']=='true' and common.settings['enable_plus']=='true' and common.settings['usertoken']:
            parameters['token'] = common.settings['usertoken']
        smilURL = False
        for item1, item2 in parameters.iteritems():
            if not smilURL:
                smilURL = 'http://s.hulu.com/select?'+item1+'='+item2
            else:
                smilURL += '&'+item1+'='+item2
        smilURL += '&bcs='+self.content_sig(parameters)
        if common.settings['proxy_enable'] == 'true':
            proxy=True
        else:
            proxy=False
        smilXML=common.getFEED(smilURL,proxy=proxy)
        if smilXML:
            smilXML=self.decrypt_SMIL(smilXML)
            if smilXML:
                smilSoup=BeautifulStoneSoup(smilXML, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
                return smilSoup
            else:
                return False
        else:
            return False
        
    def content_sig(self, parameters):
        hmac_key = 'f6daaa397d51f568dd068709b0ce8e93293e078f7dfc3b40dd8c32d36d2b3ce1'
        sorted_parameters = sorted(parameters.iteritems(), key=operator.itemgetter(0))
        data = ''
        for item1, item2 in sorted_parameters:
            data += item1 + item2
        sig = hmac.new(hmac_key, data)
        return sig.hexdigest()

    def decrypt_SMIL(self, encsmil):
        encdata = binascii.unhexlify(encsmil)
        expire_message = 'Your access to play this content has expired.'
        plus_message = 'please close any Hulu Plus videos you may be watching on other devices'
        proxy_message = 'you are trying to access Hulu through an anonymous proxy tool'
        for key in smildeckeys[:]:
            cbc = common.AES_CBC(binascii.unhexlify(key[0]))
            smil = cbc.decrypt(encdata,key[1])
            
            log( smil)
            if (smil.find("<smil") == 0):
                #log( key)
                i = smil.rfind("</smil>")
                smil = smil[0:i+7]
                return smil
            elif expire_message in smil:
                xbmcgui.Dialog().ok('Content Expired',expire_message)
                return False
            elif plus_message in smil:
                xbmcgui.Dialog().ok('Too many sessions','please close any Hulu Plus videos','you may be watching on other devices')
                return False
            elif proxy_message in smil:
                xbmcgui.Dialog().ok('Proxy Detected','Based on your IP address we noticed','you are trying to access Hulu','through an anonymous proxy tool')
                return False
    
    def queueViewComplete(self):
        u = sys.argv[0]
        u += "?mode='viewcomplete'"
        u += '&videoid="'+urllib.quote_plus(common.args.videoid)+'"'
        item=xbmcgui.ListItem("Remove from Queue")
        common.playlist.add(url=u, listitem=item)

    def getMeta( self, smilSoup ): 
        refs = smilSoup.findAll('ref')
        ref = refs[1]
        title = ref['title']
        series_title = ref['tp:series_title']
        plot = ref['abstract']
        try:season = int(ref['tp:season_number'])
        except:season = -1
        try:episode = int(ref['tp:episode_number'])
        except:episode = -1
        if episode >0 and season >0:
            displayname = series_title+' - '+str(season)+'x'+str(episode)+' - '+title
        else:
            displayname = title
        try:
            playlist = refs[0]['src']
            mpaa=re.compile('rating,([^\]]+)').findall(playlist)[0]
        except: mpaa=''
        infoLabels={ "Title":title,
                     "TVShowTitle":series_title,
                     "Plot":plot,
                     "MPAA":mpaa,
                     "Season":season,
                     "Episode":episode}
        try:
            segments = ref['tp:segments']
            if segments <> '':
                segments=segments.replace('T:','').split(',')
            else:
                segments = False
        except:segments = False
        return displayname, infoLabels, segments
                
