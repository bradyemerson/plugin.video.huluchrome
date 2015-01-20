import xbmc
import xbmcgui
import xbmcplugin
import common
import urllib


class Main:

    def __init__( self ):

        if common.args.mode.endswith('TV_play'):
            video_id = common.args.url
            finalUrl = 'http://www.hulu.com/stand_alone/%s' % (str(video_id))

            kiosk = 'yes'
            if common.settings['usekioskmode'] == 'false':
                kiosk = 'no'

            xbmc.executebuiltin("RunPlugin(plugin://plugin.program.chrome.launcher/?url=" + urllib.quote_plus(
                finalUrl) + "&mode=showSite&stopPlayback=yes&kiosk=" + kiosk + ")")
            xbmcplugin.setResolvedUrl(common.handle, True, xbmcgui.ListItem())
