#!/bin/python

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
import re, codecs, sys


regexText       = re.compile("<P>&nbsp;&nbsp;&nbsp;&nbsp;(?P<txt>.*)</P>")

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
        text = ""
        for m in regexText.finditer(html):
            text += m.group('txt')
        return text

    def parseFrontPage(self, frontpage):
        url = urllib2.urlopen(frontpage)
        html = url.read()
        html = html.replace("href!=", "href=")
        soup = BeautifulSoup(html)
        divContent = soup.findAll('ul')

        links = []
        for div in divContent:
            if div['class'] == "title_list tl_f14 tl_video":
                links.extend(div.findAll('a'))
        #print links

        for link in links:
            logging.info(link['href'])
        return [ link['href'] for link in links ]

if __name__ == "__main__":
    from optparse import OptionParser

    logging.basicConfig(level=logging.DEBUG) 

    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
        help="write report to FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
        action="store_false", dest="verbose", default=True,
        help="don't print status messages to stdout")

    (options, args) = parser.parse_args()

    parser = Parser()

    links = parser.parseFrontPage(args[0])

    for link in links[1:]:
        logging.info("Downloading "+link)
        text = parser.parse(link)
        print text
