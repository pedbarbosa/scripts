#!/usr/bin/env python2.7

import getopt
import mysql.connector
import re
import sys
import urllib2
from HTMLParser import HTMLParser


class Color:
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


def check_empty_rating():
    # Handle empty rating in Kodi
    global kodi_rating, kodi_votes
    if kodi_rating is not None:
        kodi_rating = float(kodi_rating)
    else:
        kodi_rating = 0
    if kodi_votes is None:
        kodi_votes = 0


def movie_update(count, title, old_rating, old_votes, premiered, imdb_rating):
    new_rating = float(imdb_rating.value)
    new_votes = int(imdb_rating.count.replace(',', ''))

    if old_rating > new_rating:
        new_rating = Color.LIGHTMAGENTA + '%.1f' % new_rating + Color.END
    elif old_rating < new_rating:
        new_rating = Color.LIGHTCYAN + '%.1f' % new_rating + Color.END

    if old_votes > new_votes:
        new_votes = Color.LIGHTMAGENTA + '%s' % new_votes + Color.END
    elif old_votes < new_votes:
        new_votes = Color.LIGHTCYAN + '%s' % new_votes + Color.END

    title = re.sub(r'[^\x00-\x7F]+', ' ', title)
    title = Color.GREEN + Color.UNDERLINE + title + " (" + premiered.split('-')[0] + ")" + Color.END

    if old_rating == new_rating and old_votes == new_votes:
        print("#%s " % count + title + ": %.1f* (%s)" % (old_rating, old_votes) + Color.YELLOW + " N/C" + Color.END)
    else:
        print("#%s " % count + title + ": %.1f* >> %s* (%s >> %s)" % (old_rating, new_rating, old_votes, new_votes))


def movie_error(t, m):
    m = Color.LIGHTRED + m + Color.END
    print(Color.GREEN + Color.UNDERLINE + t + Color.END + ': ' + m)


def debug_msg(m):
    if debug == 1:
        print(m)


def usage():
    print('''Usage:
    kodi_imdb.py [options]
    
Options:
    -d, --debug     Provide debug level information
    -h, --help      Show usage
    --limit         Set number of titles to process (default '100')
    --start         Set title number to start processing from (default '0')
''')


try:
    opts, args = getopt.getopt(sys.argv[1:], 'hdls:', ['help', 'debug', 'limit=', 'start='])
except getopt.GetoptError as err:
    usage()
    print(err)
    sys.exit(2)
start = debug = 0
limit = 100
for o, a in opts:
    if o in ('-h', '--help'):
        usage()
        sys.exit()
    elif o in ('-d', '--debug'):
        debug = 1
    elif o == '--limit':
        limit = a
    elif o == '--start':
        start = a
    else:
        assert False, 'unhandled option'

cnx = mysql.connector.connect(user='kodi', password='kodi',
                              host='127.0.0.1',
                              database='MyVideos107')
cursor = cnx.cursor(buffered=True)
update = cnx.cursor()

query = 'SELECT idMovie, c00 as title, votes, rating, premiered, uniqueid_value from movie_view ORDER BY c00 LIMIT %s,%s' % (start, limit)
debug_msg('Executing SQL: %s' % query)
cursor.execute(query)

stats_count = stats_success = stats_old_votes = stats_new_votes = 0

for (kodi_id, kodi_title, kodi_votes, kodi_rating, kodi_premiered, imdb_id) in cursor:
    stats_count += 1
    if imdb_id != '':
        url = 'http://www.imdb.com/title/%s' % imdb_id
        debug_msg('Fetching HTML: %s' % url)
        try:
            page = urllib2.urlopen(url)
        except urllib2.HTTPError as err:
            if err.code == 404:
                movie_error(kodi_title, 'Got 404 when trying to retrieve %s' % url)
                continue
            else:
                raise
        parser = MyHTMLParser()

        debug_msg('Processing HTML...')
        for line in page:
            parser.feed(line.decode('utf-8'))
        if parser.value != 0:
            imdb_votes = int(parser.count.replace(',', ''))
            if imdb_votes != kodi_votes:
                query = 'UPDATE movie_view SET rating="%s", votes="%s" WHERE idMovie="%s"' % (parser.value, imdb_votes, kodi_id)
                debug_msg('Updating SQL: %s' % query)
                update.execute(query)
                cnx.commit()
            movie_count = int(start) + stats_count - 1
            check_empty_rating()
            movie_update(movie_count, kodi_title, kodi_rating, kodi_votes, kodi_premiered, parser)
            stats_success += 1
            stats_old_votes += kodi_votes
            stats_new_votes += int(parser.count.replace(',', ''))
        else:
            movie_error(kodi_title, 'Problem parsing IMDb contents!')
    else:
        movie_error(kodi_title, 'No IMDb title id on Kodi!')
cnx.close()

if stats_count > 0:
    print('\nStatistics:')
    print('%s out of %s processed successfully' % (stats_success, stats_count))
if stats_old_votes != stats_new_votes:
    print('Total vote count changed from %s to %s' % (stats_old_votes, stats_new_votes))
