#!/usr/bin/env python
# coding=utf-8

import os
import re
import sys
import urlparse
import urllib
from HTMLParser import HTMLParser

#from kodiswift import Plugin, xbmc
import xbmc, xbmcplugin, xbmcaddon, xbmcgui
from bs4 import BeautifulSoup
import requests

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

addon = xbmcaddon.Addon()
params = dict(urlparse.parse_qsl(sys.argv[2][1:]))
addon_handle = int(sys.argv[1])
cache = StorageServer.StorageServer(addon.getAddonInfo('name') + '.videoid', 24 * 30)

HOST = 'http://sport.sky.de'
#BASE_PATH = '/alle-sport'
BASE_PATH = 'fussball/ligen-wettbewerbe'
BASE_URL = urlparse.urljoin(HOST, BASE_PATH)

ADDON_BASE_URL = "plugin://" + addon.getAddonInfo('id')

VIDEO_URL_FMT = "http://player.ooyala.com/player/all/{video_id}.m3u8"

USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'

def rootDir():
    html = requests.get(BASE_URL).text
    soup = BeautifulSoup(html, 'html.parser')

    for item in soup('a', 'sdc-site-directory__content'):
        label = item.span.string
        url = build_url({'action': 'showVideos', 'path': item.get('href') + '-videos', 'show_videos': 'false'})
        addDir(label, url)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

def addDir(label, url, icon=None):
    addVideo(label, url, icon, True)

def addVideo(label, url, icon, isFolder=False):
    li = xbmcgui.ListItem(label, iconImage=icon, thumbnailImage=icon)
    li.setInfo('video', {})
    li.setProperty('IsPlayable', str(isFolder))
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=isFolder)

def build_url(query):
    return ADDON_BASE_URL + '?' + urllib.urlencode(query)

def showVideos(path, show_videos):
    url = urlparse.urljoin(HOST, path)
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')

    nav = soup.find('nav', {'aria-label': 'Videos:'})

    if show_videos == 'false' and nav is not None:
        for item in nav.findAll('a'):
            xbmc.log("item = " + str(item))
            label = item.string
            url = build_url({'action': 'showVideos', 'path': item.get('href'), 'show_videos': 'true'})
            if label is not None and label != '':
                addDir(label, url)
    else:
        for item in soup('div', 'sdc-site-tiles__item sdc-site-tile sdc-site-tile--has-link'):
            link = item.find('a', {'class': 'sdc-site-tile__headline-link'})           
            label = link.span.string
            url = build_url({'action': 'playVideo', 'path': link.get('href')})
            icon = item.img.get('src')
            addVideo(label, url, icon)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

def getVideoIdFromCache(path):
    return cache.cacheFunction(getVideoId, path)

def getVideoId(path):
    video_id = None

    url = urlparse.urljoin(HOST, path)
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')

    div = soup.find('div', {'class': 'sdc-article-video'})
    if div is not None:
        video_id = div.get('data-sdc-video-id')

    if video_id is None:
        scripts = soup.findAll('script')
        for script in scripts:
            script = script.text
            match = re.search('data-sdc-video-id="([^"]*)"', script)
            if match is not None:
                video_id = match.group(1)

    return video_id

def playVideo(path):
    video_id = getVideoId(path)
    if video_id is not None: 
        li = xbmcgui.ListItem()
        li.setMimeType('application/x-mpegURL')        
        li.setProperty("inputstream.adaptive.manifest_type", "hls")
        li.setProperty('inputstreamaddon', 'inputstream.adaptive')
        li.setPath(VIDEO_URL_FMT.format(video_id=video_id) + "|" + USER_AGENT)

        xbmcplugin.setResolvedUrl(addon_handle, True, li)

if __name__ == '__main__':
    if 'action' in params:

        xbmc.log("params = " + str(params))

        if params.get('action') == 'showVideos':
            showVideos(params.get('path'), params.get('show_videos'))
        elif params.get('action') == 'playVideo':
            playVideo(params.get('path'))
    else:
        rootDir()
