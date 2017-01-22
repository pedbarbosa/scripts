#!/usr/bin/env python2.7

import getopt
import mysql.connector
import re
import sys
import urllib2
from HTMLParser import HTMLParser


class color:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    LIGHTGRAY = '\033[37m'
    DARKGRAY = '\033[90m'
    LIGHTRED = '\033[91m'
    LIGHTGREEN = '\033[92m'
    LIGHTYELLOW = '\033[93m'
    LIGHTBLUE = '\033[94m'
    LIGHTMAGENTA = '\033[95m'
    LIGHTCYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class MyHTMLParser(HTMLParser):
    ratingCountOpen = False
    ratingValueOpen = False

    value = 0
    count = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            for att in attrs:
                if att[0] == 'itemprop' and att[1] == 'ratingValue':
                    self.ratingValueOpen = True
                if att[0] == 'itemprop' and att[1] == 'ratingCount':
                    self.ratingCountOpen = True

    def handle_endtag(self, tag):
        if tag == 'span':
            self.ratingCountOpen = False
            self.ratingValueOpen = False

    def handle_data(self, data):
        if self.ratingValueOpen:
            self.value = data
        if self.ratingCountOpen:
            self.count = data


def movie_update(count, title, rating, old_votes, xbmc_year, parser):
    old_rating = float(rating)
    new_rating = float(parser.value)
    new_votes = int(parser.count.replace(',', ''))

    if old_rating > new_rating:
        new_rating = color.LIGHTMAGENTA + "%.1f" % new_rating + color.END
    elif old_rating < new_rating:
        new_rating = color.LIGHTCYAN + "%.1f" % new_rating + color.END

    if old_votes > new_votes:
        new_votes = color.LIGHTMAGENTA + "%s" % new_votes + color.END
    elif old_votes < new_votes:
        new_votes = color.LIGHTCYAN + "%s" % new_votes + color.END

    title = re.sub(r'[^\x00-\x7F]+', ' ', title)
    title = color.GREEN + color.UNDERLINE + title + " (" + xbmc_year + ")" + color.END

    if (old_rating == new_rating and old_votes == new_votes):
        print "#%s " % count + title + ": %.1f* (%s)" % (old_rating, old_votes) + color.YELLOW + " N/C" + color.END
    else:
        print "#%s " % count + title + ": %.1f* >> %s* (%s >> %s)" % (old_rating, new_rating, old_votes, new_votes)


def movie_error(title, message):
    message = color.LIGHTRED + message + color.END
    print color.GREEN + color.UNDERLINE + title + color.END + ": " + message


def usage():
    print "Switches: -h help -s start -d debug"


try:
    opts, args = getopt.getopt(sys.argv[1:], "hds:", ["help", "debug", "start="])
except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
start = 0
debug = 0
for o, a in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-d", "--debug"):
        debug = 1
    elif o in ("-s", "--start"):
        start = a
    else:
        assert False, "unhandled option"

cnx = mysql.connector.connect(user='kodi', password='kodi',
                              host='127.0.0.1',
                              database='myvideos99')
cursor = cnx.cursor(buffered=True)
update = cnx.cursor()

query = "SELECT idMovie, c00, c04, c05, c07, c09 from movie ORDER BY c00 LIMIT %s,3000" % start
if debug == 1:
    print "Executing SQL: %s" % query
cursor.execute(query)

stats_count = stats_success = stats_old_votes = stats_new_votes = 0

for (xbmc_id, title, xbmc_votes, xbmc_rating, xbmc_year, imdb_id) in cursor:
    stats_count += 1
    if imdb_id != '':
        url = "http://www.imdb.com/title/%s" % imdb_id
        if debug == 1:
            print "Fetching HTML: %s" % url
        page = urllib2.urlopen(url)
        parser = MyHTMLParser()

        if debug == 1:
            print "Processing HTML..."
        for line in page:
            if debug == 1:
                print "Processing line: %s" % line
            parser.feed(line.decode('utf-8'))
        if parser.value != 0:
            xbmc_votes = int(xbmc_votes.replace(',', ''))
            if int(parser.count.replace(',', '')) != xbmc_votes:
                query = "UPDATE movie SET c05=\'%s\', c04=\'%s\' WHERE idMovie=\'%s\'" % (parser.value, parser.count, xbmc_id)
                if debug == 1:
                    print "Updating SQL with new rating and vote count..."
                update.execute(query)
                cnx.commit()
            movie_count = int(start) + stats_count - 1
            movie_update(movie_count, title, xbmc_rating, xbmc_votes, xbmc_year, parser)
            stats_success += 1
            stats_old_votes += xbmc_votes
            stats_new_votes += int(parser.count.replace(',', ''))
        else:
            movie_error(title, "Problem parsing IMDB contents!")
    else:
        movie_error(title, "No IMDB title id on XBMC!")

cnx.close()

if stats_count > 0:
    print "\nStatistics:"
    print "%s out of %s processed successfully" % (stats_success, stats_count)
if stats_old_votes != stats_new_votes:
    print "Total vote count changed from %s to %s" % (stats_old_votes, stats_new_votes)
