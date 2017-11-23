#!/usr/bin/env python2.7

import getopt
import mysql.connector
import re
import sys
from imdb import IMDb


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


def check_empty_rating():
    # Handle empty rating in Kodi
    global kodi_rating, kodi_votes
    if kodi_rating is not None:
        kodi_rating = float(kodi_rating)
    else:
        kodi_rating = 0
    if kodi_votes is None:
        kodi_votes = 0


def movie_details(imdb_id_no_tt):
    for _ in range(5):
        try:
            return ia.get_movie(imdb_id_no_tt)
        except KeyboardInterrupt:
            print('\nCancelled by user, while retrieving IMDB title %s' % imdb_id_no_tt)
            sys.exit()
        except IMDbDataAccessError:
            print('Error retrieving information for IMDB title %s' % imdb_id_no_tt)
            sleep(5)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            sleep(5)


def movie_update(count, title, old_rating, old_votes,
                 premiered, imdb_votes, imdb_rating):
    new_rating = float(imdb_rating)
    new_votes = int(imdb_votes)

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
        query = 'UPDATE movie_view SET rating="%s", votes="%s" WHERE idMovie="%s"' % (imdb_rating, imdb_votes, kodi_id)
        debug_msg('Updating SQL: %s' % query)
        update.execute(query)
        cnx.commit()


def movie_error(t, m):
    m = Color.LIGHTRED + m + Color.END
    print(Color.GREEN + Color.UNDERLINE + t + Color.END + ': ' + m)


def print_statistics():
    if stats_count > 0:
        print('\nStatistics:')
        print('%s out of %s processed successfully' % (stats_success, stats_count))
    if stats_old_votes != stats_new_votes:
        print('Total vote count changed from %s to %s' % (stats_old_votes, stats_new_votes))


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

query = 'SELECT idMovie, c00 as title, votes, rating, premiered, uniqueid_value from movie_view ORDER BY idMovie DESC LIMIT %s,%s' % (start, limit)
debug_msg('Executing SQL: %s' % query)
cursor.execute(query)

stats_count = stats_success = stats_old_votes = stats_new_votes = 0

ia = IMDb()

for (kodi_id, kodi_title, kodi_votes, kodi_rating, kodi_premiered, imdb_id) in cursor:
    stats_count += 1
    if imdb_id != '':
        debug_msg('Checking IMDb title %s' % imdb_id)
        movie = movie_details(imdb_id[2:])
        imdb_votes = movie['votes']
        imdb_rating = movie['rating']
        movie_count = int(start) + stats_count - 1
        check_empty_rating()
        movie_update(movie_count, kodi_title, kodi_rating, kodi_votes, kodi_premiered, imdb_votes, imdb_rating)
        stats_success += 1
        stats_old_votes += kodi_votes
        stats_new_votes += int(imdb_votes)
    else:
        movie_error(kodi_title, 'No IMDb title id on Kodi!')
cnx.close()

print_statistics()
