#------------------------------------------------------------
# getvk.py URL wrapper for vk / vkontakte videos 
#
# based in:
# pelisalacarta - XBMC Plugin
# Conector para VK Server
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#
# Modify: 2011-09-12, by Ivo Brhel
# Modify: 2012-05-03, by vdo < vdo.pure at gmail.com >
# Modify: 2014-10-23, by krysty 
#
#------------------------------------------------------------

import os, sys, re


def getVkVideos(html):
    html = html.replace("amp;","")
    videourl = ""
    regexp = re.compile(r'vkid=([^\&]+)\&')
    match = regexp.search(html)
    vkid = ""
    if match is not None:
        vkid = match.group(1)
    
    patron  = "var video_host = '([^']+)'.*?"
    patron += "var video_uid = '([^']+)'.*?"
    patron += "var video_vtag = '([^']+)'.*?"
    patron += "var video_no_flv = ([^;]+);.*?"
    patron += "var video_max_hd = '([^']+)'"
    matches = re.compile(patron,re.DOTALL).findall(html)

    video_urls = []

    if len(matches) > 0:
        for match in matches:
            if match[3].strip() == "0" and match[1] != "0":
                tipo = "flv"
                if "http://" in match[0]:
                    videourl = "%s/u%s/videos/%s.%s" % (match[0],match[1],match[2],tipo)
                else:
                    videourl = "http://%s/u%s/videos/%s.%s" % (match[0],match[1],match[2],tipo)
                
                video_urls.append(["[vk.com] FLV",videourl])

            elif match[1]== "0" and vkid != "":
                tipo = "flv"
                if "http://" in match[0]:
                    videourl = "%s/assets/videos/%s%s.vk.%s" % (match[0],match[2],vkid,tipo)
                else:
                    videourl = "http://%s/assets/videos/%s%s.vk.%s" % (match[0],match[2],vkid,tipo)
                
                video_urls.append( ["FLV [vk]",videourl])
                
            else:
                if match[4]=="0":
                    video_urls.append(["[vk.com] 240p", getMP4Link(match[0],match[1],match[2],"240.mp4")])
                elif match[4]=="1":
                    video_urls.append(["[vk.com] 240p", getMP4Link(match[0],match[1],match[2],"240.mp4")])
                    video_urls.append(["[vk.com] 360p", getMP4Link(match[0],match[1],match[2],"360.mp4")])
                elif match[4]=="2":
                    video_urls.append(["[vk.com] 240p", getMP4Link(match[0],match[1],match[2],"240.mp4")])
                    video_urls.append(["[vk.com] 360p", getMP4Link(match[0],match[1],match[2],"360.mp4")])
                    video_urls.append(["[vk.com] 480p", getMP4Link(match[0],match[1],match[2],"480.mp4")])
                elif match[4]=="3":
                    video_urls.append(["[vk.com] 240p", getMP4Link(match[0],match[1],match[2],"240.mp4")])
                    video_urls.append(["[vk.com] 360p", getMP4Link(match[0],match[1],match[2],"360.mp4")])
                    video_urls.append(["[vk.com] 480p", getMP4Link(match[0],match[1],match[2],"480.mp4")])
                    video_urls.append(["[vk.com] 720p", getMP4Link(match[0],match[1],match[2],"720.mp4")])
                else:
                    video_urls.append(["[vk.com] 240p", getMP4Link(match[0],match[1],match[2],"240.mp4")])
                    video_urls.append(["[vk.com] 360p", getMP4Link(match[0],match[1],match[2],"360.mp4")])

    return video_urls


def getMP4Link(match0,match1,match2,tipo):
    if match0.endswith("/"):
        videourl = "%su%s/videos/%s.%s" % (match0,match1,match2,tipo)
    else:
        videourl = "%s/u%s/videos/%s.%s" % (match0,match1,match2,tipo)
    return videourl
