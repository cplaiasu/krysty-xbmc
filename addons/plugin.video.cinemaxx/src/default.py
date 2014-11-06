"""
    cinemaxx.ro XBMC Addon
    Copyright (C) 2012-2014 krysty
	https://code.google.com/p/krysty-xbmc/

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import sys, os, re
import urllib, urllib2
import xbmcplugin, xbmcgui
from bs4 import BeautifulSoup
import json
import plugin, db
from resources.lib.ga import track


siteUrl		= 'http://www.cinemaxx.ro/'
searchUrl		= 'http://www.cinemaxx.ro/ajax_search.php'
newMoviesUrl	= 'http://www.cinemaxx.ro/newvideos.html'

USER_AGENT 	= 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'
ACCEPT 		= 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'

moviesIcon = os.path.join(plugin.getPluginPath(), 'resources', 'media', 'moviesIcon.png')
searchIcon = os.path.join(plugin.getPluginPath(), 'resources', 'media', 'searchIcon.png')
settingsIcon = os.path.join(plugin.getPluginPath(), 'resources', 'media', 'settingsIcon.png')

print plugin.getPluginVersion()

DB = db.DB()

track(plugin.getPluginVersion())


def MAIN():
	addDir('Categorii', siteUrl, 1, moviesIcon)
	addDir('Adaugate Recent', newMoviesUrl, 11, moviesIcon)
	addDir('Cautare', siteUrl, 2, searchIcon)
	addDir('Setari', siteUrl, 98, settingsIcon)
	addDir('Golire Cache', siteUrl, 99)
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def categories(url):
	progress = xbmcgui.DialogProgress()
	progress.create('Incarcare', 'Asteptati...')
	progress.update(1, "", "Incarcare lista - 1%", "")
	
	html = BeautifulSoup(http_req(url)).find('ul', {'class': 'pm-browse-ul-subcats'}).find_all('a')
	
	total = len(html)
	current = 1
	
	for tag in html:
		addDir(tag.get_text(), tag.get('href'), 10, '')
		
		if progress.iscanceled(): sys.exit()
		
		percent = int((current * 100) / total)
		message = "Incarcare lista - " + str(percent) + "%"
		progress.update(percent, "", message, "")
		
		current += 1
		
	progress.close()
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getMovies(url, limit=False, cat='pm-ul-browse-videos'):
	progress = xbmcgui.DialogProgress()
	progress.create('Incarcare', 'Asteptati...')
	progress.update(1, "", "Incarcare lista - 1%", "")

	list = []

	cache = False
	if plugin.getSetting("enableCache") == 'true' and not limit:
		cacheFilename = re.search('browse-(.+?)-online', url)
		cacheFilename = cacheFilename.group(1)
		cache = plugin.cacheLoad(cacheFilename, int(plugin.getSetting("cacheExpire")))
		if cache:
			list = cache

	if not cache:
		pages = BeautifulSoup(http_req(url)).find('div', {'class': 'pagination'})
		if pages and not limit:
			pages = pages.find_all('a')
			pages = max(int(x) for x in re.findall('([\d]+)', str(pages)))
		else:
			pages = 1

		count = 1
		page = 1
		total_movies = 0

		while page <= pages:
			if not limit: url = re.sub('\d+', str(page), url)
			
			html = BeautifulSoup(http_req(url)).find('ul', {'id':'pm-grid', 'class': cat}).find_all('a', {'class': 'pm-thumb-fix'})
			
			total_movies = len(html) * pages
			
			for tag in html:
				name = tag.select('img')[0].get('alt').encode('utf-8').strip()
				name = re.sub('F?f?ilm ?-?|vizioneaza|online', '', name).strip()
				
				movie = {}
				movie['name'] = name
				movie['url'] = tag.get('href')
				movie['thumbnail'] = tag.select('img')[0].get('src')
				list.append(movie)
				
				if progress.iscanceled(): sys.exit()
				
				percent = int((count * 100) / total_movies)
				if page == pages: percent = 100
				message = "Incarcare lista - " + str(percent) + "%"
				progress.update(percent, "", message, "")
				
				count += 1
			
			page += 1
			
		if plugin.getSetting("enableCache") == 'true' and not limit:
			plugin.cacheList(list, cacheFilename)

	for movie in list:
		addDir(movie['name'], movie['url'], 3, movie['thumbnail'])

	progress.close()

	xbmcplugin.endOfDirectory(int(sys.argv[1]))

	
def search():
	list = []
	
	kb = xbmc.Keyboard('', 'Search', False)
	
	lastSearch = None
	try:
		lastSearch = plugin.loadData('search')
		if lastSearch: kb.setDefault(lastSearch)
	except: pass
	
	kb.doModal()
	
	if (kb.isConfirmed()):
		inputText = kb.getText()
		
		try: plugin.saveData('search', inputText)
		except: pass
		
		if inputText == '':
			dialog = xbmcgui.Dialog().ok('Cautare', 'Nimic de cautat.')
			sys.exit()
		
		searchText = {'queryString': inputText}
		data = urllib.urlencode(searchText)
		req = urllib2.Request(searchUrl, data)
		req.add_header('User-Agent', USER_AGENT)
		req.add_header('ACCEPT', ACCEPT)
		req.add_header('Referer', 'http://www.cinemaxx.ro/search.php?keywords=%s' % urllib.quote_plus(inputText))
		response = urllib2.urlopen(req).read()
		
		html = BeautifulSoup(response).find_all('a')
		
		for tag in html:
			movie = {}
			movie['name'] = tag.select('img')[0].get('alt').encode('utf-8').strip()
			movie['url'] = tag.get('href')
			movie['thumbnail'] = tag.select('img')[0].get('src')
			list.append(movie)
	
	else: sys.exit()
	
	if list:
		for movie in list:
			addDir(movie['name'], movie['url'], 3, movie['thumbnail'])
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def http_req(url, getCookie=False):
	req = urllib2.Request(url)
	req.add_header('User-Agent', USER_AGENT)
	req.add_header('ACCEPT', ACCEPT)
	response = urllib2.urlopen(req)
	source = response.read()
	response.close()
	if getCookie:
		cookie = response.headers.get('Set-Cookie')
		return {'source': source, 'cookie': cookie}
	return source

	
def playStream(url,title,thumbnail):
	win = xbmcgui.Window(10000)
	print title
	win.setProperty('cinemaxx.playing.title', title.lower())
	
	item = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
	item.setInfo(type = "Video", infoLabels = {"title": title})
	
	xbmc.Player().play(item=url, listitem=item)
	
	return True


def selectSource(url, title='', thumbnail=''):
	progress = xbmcgui.DialogProgress()
	progress.create('Incarcare', 'Asteptati...')
	progress.update(1, "", "Cautare surse video...", "")
	
	sources = getSources(url)
	
	progress.close()
	
	if not sources:
		return xbmcgui.Dialog().ok("", "Sursele video nu au fost gasite.")
	
	labels = []
	
	for item in sources:
		labels.append(item['name'])
	
	dialog = xbmcgui.Dialog()
	
	index = dialog.select('Selectati sursa video', labels)
	if index > -1:
		playStream(sources[index]['url'], title, thumbnail)
	else:
		return


def getSources(url):
	sources = []
	
	#formatare html pentru a obtine url-ul pentru playerul video, din cauza reclamelor javascript
	html = BeautifulSoup(http_req(url)).find_all('script', {'type': 'text/javascript'})
	html = "".join(line.strip() for line in str(html).split("\n"))
	html = re.findall(r'\$\.ajax\({.+?data: {(.+?)}', html)
	html = html[1].replace('"', '').split(',')
	params = {}
	for parameter in html:
		key, value = parameter.split(':')
		params[key] = value.strip()
	#in sfarsit url-ul pentru playerul video
	url = '%sajax.php?p=video&do=getplayer&vid=%s' % (siteUrl, params['vid'])
	
	url = BeautifulSoup(http_req(url)).find('iframe').attrs['src']
	
	srcMailRu = None
	try: srcMailRu = resolveMailRu(url)
	except: pass

	if srcMailRu:
		for source in srcMailRu[0]:
			name = '%s %s' % ('[mail.ru]', source['key'])
			link = '%s|Cookie=%s' % (source['url'], urllib.quote_plus(srcMailRu[1]))
			item = {'name': name, 'url': link}
			sources.append(item)

	srcVk = None
	try:
		from resources.lib.getvk import getVkVideos
		srcVk = getVkVideos(http_req(url))
	except: pass
	
	if srcVk:
		for vk in srcVk:
			item = {'name': vk[0], 'url': vk[1]}
			sources.append(item)
	
	return sources


def resolveMailRu(url):
	source = BeautifulSoup(http_req(url)).find_all('script', {'type': 'text/javascript'})
	jsonUrl = re.search(r'"metadataUrl":"(.+?)"', str(source)).group(1)
	req = http_req(jsonUrl, True)
	jsonSource = json.loads(req['source'])
	return [jsonSource['videos'], req['cookie']]

	
def addDir(name, url, mode, thumbnail='', folder=True):
	ok = True
	params = {'name': name, 'mode': mode, 'url': url, 'thumbnail': thumbnail}

	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
	
	if not folder:
		liz.setProperty('isPlayable', 'true')
		liz.setProperty('resumetime', str(0))
		liz.setProperty('totaltime', str(1))
		
	liz.setInfo(type="Video", infoLabels = {"title": name})

	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = set_params(params), listitem = liz, isFolder = folder)
	return ok


def clearCache():
	if plugin.clearCache():
		xbmcgui.Dialog().ok('', 'Cache-ul a fost curatat.')
	else:
		xbmcgui.Dialog().ok('', 'Eroare. Incercati din nou.')


def set_params(dict):
	out = {}
	for key, value in dict.iteritems():
		if isinstance(value, unicode):
			value = value.encode('utf8')
		elif isinstance(value, str):
			value.decode('utf8')
		out[key] = value
	return sys.argv[0] + '?' + urllib.urlencode(out)
	
	
def get_params():
	param = {'default': 'none'}
	paramstring = sys.argv[2]
	if len(paramstring) >= 2:
			params = sys.argv[2]
			cleanedparams = params.replace('?','')
			if (params[len(params)-1] == '/'):
				params = params[0:len(params)-2]
			pairsofparams = cleanedparams.split('&')
			param = {}
			for i in range(len(pairsofparams)):
				splitparams = {}
				splitparams = pairsofparams[i].split('=')
				if (len(splitparams)) == 2:
					param[splitparams[0]] = splitparams[1]
	return param


params = get_params()

mode = int(params.get('mode', 0))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
thumbnail = urllib.unquote_plus(params.get('thumbnail', ''))


if mode: print 'Mode: ' + str(mode)
if url: print 'URL: ' + str(url)


if mode == 0 or not url or len(url) < 1: MAIN()
elif mode == 1: categories(url)
elif mode == 2: search()
elif mode == 3: selectSource(url, name, thumbnail)
elif mode == 10: getMovies(url)
elif mode == 11: getMovies(url, True, 'pm-ul-new-videos')
elif mode == 98: plugin.openSettings()
elif mode == 99: clearCache()
