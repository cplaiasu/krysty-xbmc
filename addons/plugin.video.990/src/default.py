"""
    990.ro XBMC Addon
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
import plugin, db
from resources.lib.BeautifulSoup import BeautifulSoup
from resources.lib.ga import track


siteUrl		= 'http://www.990.ro/'
searchUrl	= 'http://www.990.ro/functions/search3/live_search_using_jquery_ajax/search.php'
tvShowsUrl	= 'http://www.990.ro/seriale-lista.html'
moviesUrl	= 'http://www.990.ro/toate-filmele.php'

USER_AGENT 	= 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'
ACCEPT 		= 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'


TVshowsIcon = os.path.join(plugin.getPluginPath(), 'resources', 'media', 'tvshowsicon.png')
MoviesIcon = os.path.join(plugin.getPluginPath(), 'resources', 'media', 'moviesicon.png')
SearchIcon = os.path.join(plugin.getPluginPath(), 'resources', 'media', 'searchicon.png')
InfoIcon = os.path.join(plugin.getPluginPath(), 'resources', 'media', 'inficon.png')
SettingsIcon = os.path.join(plugin.getPluginPath(), 'resources', 'media', 'settingsicon.png')

print plugin.getPluginVersion()

DB = db.DB()

track(plugin.getPluginVersion())


def MAIN():
	addDir('TV Shows',tvShowsUrl,4,TVshowsIcon)
	addDir('Movies',moviesUrl,10,MoviesIcon)
	addDir('Search',siteUrl,16,SearchIcon)
	addDir('Settings',siteUrl,99,SettingsIcon)
	addDir('Clear Cache',siteUrl,18)
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def TVSHOWS(url):
	import string
	AZ = (ltr for ltr in string.ascii_uppercase)
	
	addDir('All',url,1,TVshowsIcon)
	addDir('Last Added',url,5,TVshowsIcon)
	addDir('Search',url,15,TVshowsIcon)
	addDir('[1-9]',url,17,TVshowsIcon)
	for character in AZ:
		addDir(character,url,17,TVshowsIcon)
		
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	

def getTVshows(url,order=None):
	progress = xbmcgui.DialogProgress()
	progress.create('Progress', 'Please wait...')
	progress.update(1, "", "Loading list - 1%", "")
	
	div = BeautifulSoup(http_req(url)).find("div", {"id": "tab1"})

	if not order:
		tvs = div.findAll("a")	
	else:
		tvs = [s.parent for s in div.findAll("a", text = re.compile(r"^" + order + ".+?$"))]
	
	current = 0
	total = len(tvs)

	while current <= total - 1:
		title = htmlFilter(tvs[current].text)
		link = urlFilter(tvs[current]['href'])

		addDir(title, link, 2)

		if progress.iscanceled(): sys.exit()

		percent = int(((current + 1) * 100) / total)
		message = "Loading list - " + str(percent) + "%"
		progress.update(percent, "", message, "")

		current += 1
	
	progress.close()
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getSeasons(tvshow, url):
	progress = xbmcgui.DialogProgress()
	progress.create('Progress', 'Please wait...')
	progress.update(1, "", "Loading list - 1%", "")
	
	seasons = re.findall(r"<img src='.+?' alt='Sezonul (.+?)'>", http_req(url))
	thumb = re.findall(r"<img src='../(.+?)'", http_req(url))
	if thumb: thumbnail = siteUrl + thumb[0]
	else: thumbnail = ''

	total = len(seasons)
	current = 0

	while current <= total - 1:
		season_nr = str(seasons[current]).zfill(2)		
		name = 'Season %s' % season_nr
		
		addDir(name,url,3,thumbnail,tvshow,season_nr)
		
		if progress.iscanceled(): sys.exit()
		
		percent = int(((current + 1) * 100) / total)
		message = "Loading list - " + str(percent) + "%"
		progress.update( percent, "", message, "" )
		
		current += 1
			
	progress.close()
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

		
def getEpisodes(url,season,title,thumbnail):
	progress = xbmcgui.DialogProgress()
	progress.create('Progress', 'Please wait...')
	progress.update(1, "", "Loading list - 1%", "")

	title = re.sub('\(.+?\)', '', title).strip()
	
	list = []
	
	cache = False
	if plugin.getSetting("enableCache") == 'true':
		cacheFilename = '%s-s%s-episodes' % (re.sub(' ', '-', title), season)
		cache = plugin.cacheLoad(cacheFilename, int(plugin.getSetting("cacheExpire")))
		if cache:
			list = cache

	if not cache:		
		div = htmlFilter(str(BeautifulSoup(http_req(url)).find("div", {"id": "content"})), True)
		
		episodes = re.findall(r'Sezonul '+season+', Episodul (.+?)</div>.+?<a href="seriale2-([\d]+-[\d]+)-.+?.html" class="link">(.+?)</a>', div)

		if episodes:
			total = len(episodes)
		else:
			episodes = re.findall(r'ma;">([\d]+)</div>.+?<a href="seriale2-([0-9]+-[0-9]+)-.+?.html" class="link">(.+?)</a>', div)
			total = len(episodes)

		current = 0

		while current <= total - 1:
			
			ep_num = episodes[current][0]
			ep_name = episodes[current][2]
			
			if ep_name == str(re.findall('(Episodul [-0-9]*)',ep_name)).strip('[]').strip('"\''): ep_name = ''
			
			tvshow = {}
			tvshow['url'] = siteUrl + 'player-serial-' + episodes[current][1] + '-sfast.html'
			tvshow['thumbnail'] = thumbnail
			tvshow['title'] = title
			tvshow['season'] = season
			tvshow['ep_num'] = ep_num
			tvshow['ep_name'] = ep_name
			list.append(tvshow)
			
			if progress.iscanceled(): sys.exit()
			
			percent = int(((current + 1) * 100) / total)
			message = "Loading list - " + str(percent) + "%"
			progress.update(percent, "Enabling cache storage will speed up future loads.", message, "")
			
			current += 1
			
		if plugin.getSetting("enableCache") == 'true':
			plugin.cacheList(list, cacheFilename)

	for tvshow in list:
		name = 'Episode %s %s' % (tvshow['ep_num'], tvshow['ep_name'])
		
		addDir(name,tvshow['url'],8,tvshow['thumbnail'],tvshow['title'],tvshow['season'],tvshow['ep_num'],tvshow['ep_name'],folder=False)
		
	progress.close()

	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	

def lastAdded(cat):
	progress = xbmcgui.DialogProgress()
	progress.create('Progress', 'Please wait...')
	progress.update(1, "", "Loading list - 1%", "")

	div = htmlFilter(str(BeautifulSoup(http_req(siteUrl)).findAll("div", {"id": "tab1"})), True)
	
	if cat == 'tvshows':
		results = re.findall(r'<a class="link" href="(seriale2)-([0-9]+-[0-9]+)-.+?.html">(.+?)</a>.+?">(.+?)</div></div>', div)
	elif cat == 'movies':
		results = re.findall(r'<a class="link" href="(filme)-(.+?).html">(.+?)</a>.+?">(.+?)</div>', div)
	
	total = len(results)
	current = 0

	while current <= total-1:
		
		type = results[current][0]
		link = results[current][1]
		title = results[current][2]
		ep_year = results[current][3]
		
		if type == 'seriale2':
			eps = re.findall(r'S(\d+)E(\d+)', ep_year)
			if eps:
				season = eps[0][0]
				episode = eps[0][1]
			else:
				season = ''
				episode = ''
			
			name = '%s %sx%s' % (title, season, episode)
			url = siteUrl + 'player-serial-' + link + '-sfast.html'
			
			addDir(name,url,8,"",title,season,episode,folder=False)
		
		elif type == 'filme':
			year = re.findall('(\d{4,4})', ep_year)		
			name = '%s (%s)' % (title, year[0])
			url = siteUrl + 'filme-' + link + '.html'
			
			addDir(name,url,8,"",name,folder=False)

		if progress.iscanceled(): sys.exit()
		
		percent = int(((current + 1) * 100) / total)
		message = "Loading list - " + str(percent) + "%"
		progress.update(percent, "", message, "")
		
		current += 1
	
	progress.close()
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	

def MOVIES(url,order=None):
	if order == 'year':
		div = BeautifulSoup(http_req(url)).findAll("div", {"id": "filtre"})[1].findAll("a", attrs = {"class": None})
		for a in div:
			addDir(a.text, moviesUrl + a['href'], 9, MoviesIcon)
	
	elif order == 'genre':
		div = BeautifulSoup(http_req(url)).find("div", {"id": "filtre"}).findAll("a", attrs = {"class": None})
		for a in div:
			addDir(plugin.ro2en(a.text), moviesUrl + a['href'], 9, MoviesIcon)
	
	else:
		addDir('Search',url,14,MoviesIcon)
		addDir('Last Added',url,6,MoviesIcon)
		addDir('By Year',url,11,MoviesIcon)
		addDir('By Genre',url,12,MoviesIcon)
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getMovies(url):
	progress = xbmcgui.DialogProgress()
	progress.create('Progress', 'Please wait...')
	progress.update(1, "", "Loading list - 1%", "")
	
	soup = BeautifulSoup(http_req(url))
	
	pages = str(soup.find("div", {"id": "numarpagini"}))
	pages = max(int(x) for x in re.findall(r'([\d]+)</a>', pages))
	page = int(re.search('pagina=(\d+)', url).group(1))
	
	div = soup.find("div", {"id": "content"})
	links  = div.findAll("a", {"class": "link"})
	thumbs = re.findall(r'<img src="../(.+?)"', str(div))
	years = re.findall(r'Aparitie: ?(\d+)', str(div))
	
	total = len(links)
	current = 0
	
	while current <= total - 1:
		name = "%s (%s)" % (htmlFilter(links[current].text), years[current])
		link = urlFilter(links[current]['href'])
		thumbnail = siteUrl + thumbs[current]
		
		addDir(name, link, 8, thumbnail, name, folder=False)
		
		if progress.iscanceled(): sys.exit()
		
		percent = int(((current + 1) * 100) / total)
		message = "Loading list - " + str(percent) + "%"
		progress.update(percent, "", message, "")
				
		current += 1
	
	if not page == pages:
		url = re.sub('pagina=\d+', 'pagina=' + str(page + 1), url)
		addDir("Next Page >>", url, 9)
	
	progress.close()
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

	
def SEARCH(cat):
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
			dialog = xbmcgui.Dialog().ok('Search', 'There is nothing to search.')
			sys.exit()

		progress = xbmcgui.DialogProgress()
		progress.create('Progress', 'Please wait...')
		progress.update(1, "", "Loading list - 1%", "")
		
		searchText = {'kw': inputText}
		req = urllib2.Request(searchUrl, urllib.urlencode(searchText))
		req.add_header('User-Agent', USER_AGENT)
		req.add_header('Cache-Control', 'no-transform')
		response = htmlFilter(urllib2.urlopen(req).read())
		
		if cat == 'all':
			results = re.findall(r'<a href="(.+?)-(.+?)-online-download.html">.+?<div id="rest">(.+?)<div id="auth_dat">', response)
			thumb = re.findall(r'<img class="search" .+? src="../(.+?)"', response)
		else:
			results = re.findall(r'<a href="('+cat+')-(.+?)-online-download.html">.+?<div id="rest">(.+?)<div id="auth_dat">', response)
			thumb = re.findall(r'<a href="'+cat+'-.+?<img class="search" .+? src="../(.+?)"', response)
		
		total = len(results)
		current = 0
		
		while current <= total - 1:
			
			if results[current][0] == 'seriale':
				name = re.sub('\(', ' (', results[current][2])
				url = '%sseriale-%s-online-download.html' % (siteUrl, results[current][1])
				thumbnail = siteUrl + thumb[current]
				title = re.sub('\(.+?\)', '', name).strip()
				
				addDir(name,url,2,thumbnail,title)
			
			elif results[current][0] == 'filme':
				title = re.sub('\(', ' (', results[current][2])
				url = '%sfilme-%s-online-download.html' % (siteUrl, results[current][1])
				thumbnail = siteUrl + thumb[current]
				
				addDir(title,url,8,thumbnail,title,folder=False)
			
			if progress.iscanceled(): sys.exit()
			
			percent = int(((current + 1) * 100) / total)
			message = "Loading list - " + str(percent) + "%"
			progress.update( percent, "", message, "" )
			
			current += 1
			
		progress.close()
	
	else: sys.exit()
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def http_req(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', USER_AGENT)
	req.add_header('Accept', ACCEPT)
	req.add_header('Cache-Control', 'no-transform')
	response = urllib2.urlopen(req)
	source = response.read()
	response.close()
	return source


def getTrailer(url):
	trailerframe = re.findall(r"<iframe width='595' height='335' src='.+?/embed/(.+?)'", http_req(url))
	if trailerframe:
		yt = youtube_video('http://www.youtube.com/watch?v=' + trailerframe[0])
		if yt:
			return yt + '?.mp4'
		else: return False
	else: return False


def youtube_video(url):
	try:
		conn = urllib2.urlopen(url)
		encoding = conn.headers.getparam('charset')
		content = conn.read().decode(encoding)
		s = re.findall(r'"url_encoded_fmt_stream_map": "([^"]+)"', content)
		if s:
			import HTMLParser
			s = s[0].split(',')
			s = [a.replace('\\u0026', '&') for a in s]
			s = [urllib2.parse_keqv_list(a.split('&')) for a in s]
			n = re.findall(r'<title>(.+) - YouTube</title>', content)
			s, n = (s or [], HTMLParser.HTMLParser().unescape(n[0]))
			for z in s:
				if z['itag'] == '18':
					if 'mp4' in z['type']:
						ext = '.mp4'
					elif 'flv' in z['type']:
						ext = '.flv'
					try: link = urllib.unquote(z['url'] + '&signature=%s' % z['sig'])
					except: link = urllib.unquote(z['url'])
			return link
	except: return False


def playTrailer(url,title='',thumbnail=''):
	progress = xbmcgui.DialogProgress()
	progress.create('Progress', 'Please wait...')
	
	trailerUrl = getTrailer(url)
	if trailerUrl:
		title = '%s Trailer' % title
		liz = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
		liz.setInfo(type = "Video", infoLabels = {"title": title})
		xbmc.Player().play(item=trailerUrl, listitem=liz)
	else:
		xbmcgui.Dialog().ok("", "Error: trailer link not available!")
	
	progress.close()
	
	
def playStream(url,title,thumbnail,season='',episode='',ep_name='',subtitle=''):
	win = xbmcgui.Window(10000)
	win.setProperty('990.playing.title', title.lower())
	win.setProperty('990.playing.season', str(season))
	win.setProperty('990.playing.episode', str(episode))
	win.setProperty('990.playing.subtitle', subtitle)
	
	if season and episode:
		title = ('%s %sx%s %s' % (title, season, episode, ep_name)).strip()
	
	item = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
	item.setInfo(type = "Video", infoLabels = {"title": title})
	item.setPath(url)
	
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
	return True


def selectSource(url,title='',thumbnail='',season='',episode='',ep_name=''):
	sources = getSources(url)
	if not sources:
		return xbmcgui.Dialog().ok("", "Error: video link(s) not available!")
	else:
		labels = []
		for item in sources:
			labels.append(item['name'])
		dialog = xbmcgui.Dialog()
		index = dialog.select('Choose your stream', labels)
		if index > -1:
			playStream(sources[index]['url'], title, thumbnail, season, episode, ep_name, sources[index]['subtitle'])
		else:
			return
	
	
def getSources(url):
	sources = []
	try:
		quality = ''
		if(re.search('filme', url)):
			quality = re.search(r'Calitate film: nota <b>(.+?)</b>', http_req(url))
			movieId = re.search('-([\d]+)-', url)
			url = siteUrl + 'player-film-' + movieId.group(1) + '-sfast.html'

		match = re.search(r'http://(?:www.)?(?:fastupload|superweb)(?:.rol)?.ro/?(?:video)?/(?:.+?).html?', http_req(url))
		url = match.group(0)
		match = re.search(r"'file': '(.+?)',", http_req(url))
		videoLink = match.group(1) + '|referer=' + url
		
		if(quality == ''):
			item = {'name': 'Play Video', 'url': videoLink, 'subtitle': getSubtitle(url)}
		else:
			item = {'name': 'Play Video (Quality:'+quality.group(1)+')', 'url': videoLink, 'subtitle': getSubtitle(url)}
		
		sources.append(item)
		
		return sources
	except:
		return False


def getSubtitle(url):
	subtitle = ''
	try:
		if plugin.getSetting("enableSub") == 'true':
			page = str(BeautifulSoup(http_req(url)).findAll("script"))
			page = ''.join(page.split())
			match = re.findall('\'tracks\':\[{\'file\':"http:\/\/superweb\.rol\.ro\/video\/jw6\/(.+?)",', page)
			if match:
				sub_url = 'http://superweb.rol.ro/video/jw6/' + match[0]
				sub_tmp = os.path.join(xbmc.translatePath("special://temp"), match[0])
				with open(sub_tmp, 'w') as f:
					f.write(http_req(sub_url))
				subtitle = match[0]
	except: pass
	return subtitle


def addDir(name,url,mode,thumbnail='',title='',season='',episode='',episode_name='',folder=True):
	ok = True
	params = {'name': name, 'mode': mode, 'url': url, 'thumbnail': thumbnail}

	params['title'] = title
	params['season'] = season
	params['episode'] = episode
	params['ep_name'] = episode_name

	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
	
	if not folder:
		liz.setProperty('isPlayable', 'true')
		liz.setProperty('resumetime', str(0))
		liz.setProperty('totaltime', str(1))
		
		if not season:
			contextMenuItems = []
			trailer = {'url': url, 'title': title, 'mode': 19, 'thumbnail': thumbnail}
			contextMenuItems.append(('Play Trailer', 'XBMC.RunPlugin(%s)' % set_params(trailer)))
			liz.addContextMenuItems(contextMenuItems, replaceItems=True)
		
	liz.setInfo(type="Video", infoLabels = {"title": name})

	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = set_params(params), listitem = liz, isFolder = folder)
	return ok


def clearCache():
	if plugin.clearCache():
		xbmcgui.Dialog().ok('', 'Cache storage successfully cleared.')
	else:
		xbmcgui.Dialog().ok('', 'Something went wrong.')


def htmlFilter(htmlstring, trimspaces = False):
	hex_entity_pat = re.compile('&#x([^;]+);')
	hex_entity_fix = lambda x: hex_entity_pat.sub(lambda m: '&#%d;' % int(m.group(1), 16), x)
	htmlstring = str(BeautifulSoup(hex_entity_fix(htmlstring), convertEntities=BeautifulSoup.ALL_ENTITIES))
	if trimspaces:
		htmlstring = "".join(line.strip() for line in htmlstring.split("\n"))
	return htmlstring


def urlFilter(url):
	if not re.search(siteUrl, url):
		url = siteUrl + url
	return url


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
title = urllib.unquote_plus(params.get('title', ''))
thumbnail = urllib.unquote_plus(params.get('thumbnail', ''))
season = urllib.unquote_plus(params.get('season', ''))
episode = urllib.unquote_plus(params.get('episode', ''))
ep_name = urllib.unquote_plus(params.get('ep_name', ''))


if mode: print 'Mode: ' + str(mode)
if url: print 'URL: ' + str(url)


if mode == 0 or not url or len(url) < 1: MAIN()
elif mode == 1: getTVshows(url)
elif mode == 2: getSeasons(name,url)
elif mode == 3: getEpisodes(url,season,title,thumbnail)
elif mode == 4: TVSHOWS(url)
elif mode == 5: lastAdded('tvshows')
elif mode == 6: lastAdded('movies')
elif mode == 8: selectSource(url,title,thumbnail,season,episode,ep_name)
elif mode == 9: getMovies(url)
elif mode == 10: MOVIES(url)
elif mode == 11: MOVIES(url,order='year')
elif mode == 12: MOVIES(url,order='genre')
elif mode == 14: SEARCH('filme')
elif mode == 15: SEARCH('seriale')
elif mode == 16: SEARCH('all')
elif mode == 17: getTVshows(url,order=name)
elif mode == 18: clearCache()
elif mode == 19: playTrailer(url,title,thumbnail)
elif mode == 99: plugin.openSettings()
