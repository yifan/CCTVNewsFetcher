#!/bin/python
# vim: set fileencoding=utf8 :


###############################################################################
#
# Fetch CCTV news text and video
#
# Copyright (c) freqyifan at gmail dot com
###############################################################################


# TODO check if the text is complete, and go to 'more' page if necessary
# TODO download video

import logging
from BeautifulSoup import BeautifulSoup
import urllib2
import re, codecs, sys, os


regex06Text       = re.compile("<p align=left>(?P<txt>.*?)</p>", re.S|re.I)
regex07Text       = re.compile("<p>(?P<txt>.*?)</p>", re.S|re.I)
regex06List     = re.compile(u"<!--列表开始-->(?P<txt>.*)<!--列表结束 -->".encode('gb2312'))
tag06ListStart  = u"<!--列表开始-->".encode('gb2312')
tag06ListEnd    = u"<!--列表结束 -->".encode('gb2312')
regex07Video    = re.compile("")

regexDate       = re.compile("http://news.cctv.com/news/xwlb/(?P<dir>\d+)/index.shtml")

regex06Media    = re.compile('media 300k"\s+href="(?P<url>.*?)"', re.I)

class Extractor:
    """ Extract content belongs to specific tag
        thetag  - tag name, e.g. 'div'
        fulltag - regular expression to match specific tag, 
                    e.g. '<div id="none">' 
    """
    def __init__(self, thetag, fulltag):
        self.regexStart = re.compile(fulltag)
        self.regexTag = re.compile("<(?P<tag>/?%s)" % thetag)

    def extract(self, text):
        match = ""
        ctext = text
        m = self.regexStart.search(ctext)
        while m:
            ctext = ctext[m.end():]
            mtag = self.regexTag.search(ctext)
            level = 0
            endt = 0
            while mtag:
                if mtag.group('tag')[0] == '/':
                    if level == 0:
                        endt = mtag.start()
                        break
                    else:
                        level -= 1
                else:
                     level += 1
            match += ctext[:endt]
            ctext = ctext[endt:]
            m = self.regexStart.search(ctext)
        return match



class Parser:
    def __init__(self):
        pass

    def parse(self, page):
        url = urllib2.urlopen(page)
        raw = url.read()
        extractor = Extractor('div', '<div\s+id="md_major_article_content".*>')
        html = extractor.extract(raw)
        if self.pagetype == 0:
            regex = regex07Text
            
        elif self.pagetype == 1:
            regex = regex06Text
            m = regex06Media.search(raw)
            filename = page.replace(":","_").replace("/","_").rstrip(".shtml")
            if m:
                mediaurl = m.group('url')
                mediaurl = mediaurl.replace("www.cctv.com/video","v.cctv.com/flash")
                mediaurl = mediaurl.replace(".shtml",".flv")
                logging.info(mediaurl)
                if os.path.exists(os.path.join(self.dir, filename)):
                    logging.info("Skipping exsiting download")
                else:
                    os.system("wget -O %s.flv %s" % (os.path.join(self.dir, filename), mediaurl))
            else:
                logging.info("No video for this news")


        if html:
            text = ""
            for m in regex.finditer(html):
                text += m.group('txt') + "\n"
            shtml = open(os.path.join(self.dir, filename+".raw"), "w")
            shtml.write(text)
            shtml.close()
            return text
        else:
            logging.error("Cannot extract context from this page")
            return ""


    def parseFrontPage(self, frontpage):
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

        url = urllib2.urlopen(frontpage)
        html = url.read()
        html = html.replace("href!=", "href=")
        
        if html.find('title_list tl_f14 tl_video') >= 0:

            soup = BeautifulSoup(html)
            divContent = soup.findAll('ul')

            links = []
            for div in divContent:
                if div['class'] == "title_list tl_f14 tl_video":
                    links.extend(div.findAll('a'))

            for link in links:
                logging.info(link['href'])

            self.pagetype = 0

            return [ link['href'] for link in links ]

        elif html.find(tag06ListStart) >= 0:
            st = html.find(tag06ListStart) + len(tag06ListStart)
            en = html.find(tag06ListEnd)

            extracted = html[st:en]
            soup = BeautifulSoup(extracted)
            print soup
            links = []
            for div in soup.findAll('td', attrs={'class':'big'}):
                links.extend(div.findAll('a'))
            #print links

            for link in links:
                logging.info(link['href'])

            self.pagetype = 1

            return [ link['href'] for link in links ]
        else:
            logging.error("Unrecognized frontpage. Parsing failed")
            return []

if __name__ == "__main__":
    usage = """ 
    Usage: 
      python fetch.py [url of index page]
      e.g. 
        python fetch.py http://news.cctv.com/news/xwlb/20090625/index.shtml
    """

    from optparse import OptionParser
    from datetime import date, timedelta, datetime

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s") 

    parser = OptionParser(usage=usage)
    parser.add_option("-f", "--file", dest="filename",
        help="write report to FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
        action="store_false", dest="verbose", default=True,
        help="don't print status messages to stdout")
    
    (options, args) = parser.parse_args()

    parser = Parser()

    stdate = datetime.strptime(args[0], "%Y%m%d").date()
    endate = datetime.strptime(args[1], "%Y%m%d").date()

    oneday = timedelta(1)
    cudate = stdate
    while True:
        url = "http://news.cctv.com/news/xwlb/%s/index.shtml" % cudate.strftime("%Y%m%d")

        parser.dir = cudate.strftime("%Y%m%d")
        links = parser.parseFrontPage(url)

        for link in links[1:]:
            if link.strip() == "": continue
            logging.info("Downloading "+link)
            text = parser.parse(link)
            logging.info(text.decode('gb2312', 'ignore'))

        if cudate == endate:
            logging.info("DONE.")
            break
        cudate += oneday
