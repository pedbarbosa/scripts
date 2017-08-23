#!/usr/bin/env python3
from pymediainfo import MediaInfo
import os
import pickle
import importlib


def exit_with_msg(m):
    print(m)
    exit(1)


def read_pickle(f):
    with open(f, 'rb') as handle:
        return pickle.load(handle)


def update_pickle(f, d):
    with open(f, 'wb') as handle:
        pickle.dump(d, handle)


def track_codec(i):
    if i.format == 'HEVC':
        return 'x265'
    elif i.format == 'AVC':
        return 'x264'
    elif i.format == 'MPEG-4 Visual' or i.format == 'MPEG Video':
        return 'mpeg'
    else:
        return ''


def track_resolution(i):
    if i.height >= 800:
        return '1080p'
    elif 640 <= i.height < 800:
        return '720p'
    elif i.height < 640:
        return 'sd'
    else:
        return ''


def episode_badge(i, n):
    if (i['x265_1080p'] + i['x264_1080p']) == n:
        return '1080p'
    elif (i['x265_720p'] + i['x264_720p'] + i['mpeg_720p']) == n:
        return '720p'
    elif (i['x265_sd'] + i['x264_sd'] + i['mpeg_sd']) == n:
        return 'SD'
    else:
        return 'Mix'


if not importlib.util.find_spec('progressbar'):
    exit_with_msg('Error: Python module not found. Install progressbar2.')
else:
    import progressbar

# Variable initialisation
scan_directory = html_file = report_html = recode_html = pickle_file = recode = ''
codec_override = video_extensions = []
episodes = dict()
config_file = os.path.expanduser('~') + '/.tvreport'

# Check configuration file
if not os.path.isfile(config_file):
    exit_with_msg('Error: Config file %s missing. Copy tvreport.cfg to %s and configure as required.' % (config_file, config_file))
else:
    exec(compile(open(config_file, "rb").read(), config_file, 'exec'))

if not os.path.isdir(scan_directory):
    exit_with_msg('Error: %s is not a directory or doesn\'t exist. Check your %s config file.' % (scan_directory, config_file))

# Checking if a scan has been run previously
if os.path.isfile(pickle_file):
    episodes = read_pickle(pickle_file)
    # Check if previously scanned files have been deleted
    episodes_pickle = len(episodes)
    print('Found %s episodes from previous scan(s) cached, scanning for removed episodes...' % episodes_pickle)
    scan_bar_progress = 0
    scan_bar = progressbar.ProgressBar(max_value=episodes_pickle)
    for episode_path in list(episodes):
        scan_bar_progress += 1
        if not os.path.exists(episode_path):
            del episodes[episode_path]
        scan_bar.update(scan_bar_progress)
    scan_bar.update(episodes_pickle)
    print('\nFinished existing file scan, %s episodes removed.' % (episodes_pickle - len(episodes)))
    update_pickle(pickle_file, episodes)
    check_episodes = dict(episodes)
shows = dict()
errors = dict()

# Processing root directory
episodes_directories = len(next(os.walk(scan_directory))[1])
scan_bar_progress = 0
scan_bar = progressbar.ProgressBar(max_value=episodes_directories)
print('Found %s directories, scanning for episodes...' % episodes_directories)

for dirpath, dirnames, filenames in os.walk(scan_directory, topdown=True):
    scan_bar.update(scan_bar_progress)
    videodir = os.path.basename(dirpath)
    depth = dirpath[len(scan_directory) + len(os.path.sep):].count(os.path.sep)

    # Processing show directory
    if depth == 0:
        if len(videodir) != 0:
            scan_bar_progress += 1
        # Process each video file
        for video in filenames:
            if video.endswith(tuple(video_extensions)):
                episode_path = os.path.join(dirpath, video)
                episode_size = os.path.getsize(episode_path)
                episode_rescan = 1

                # Check if file has been scanned previously
                if episode_path in episodes:
                    episode_old = episodes.get(episode_path)
                    # Check if file size matches previous scan
                    if episode_size == episode_old['size']:
                        episode_rescan = 0
                episode_codec = ''
                episode_resolution = ''
                episode_format = ''

                # Run mediainfo if file hasn't been scanned previously or has changed
                if episode_rescan == 1:
                    # or no episode_path in episodes
                    videoinfo = MediaInfo.parse(episode_path)
                    for track in videoinfo.tracks:
                        if track.track_type == 'Video':
                            episode_codec = track_codec(track)
                            episode_resolution = track_resolution(track)
                            episode_format = episode_codec + '_' + episode_resolution
                            # Codec and/or resolution does not match the criteria above
                            if len(episode_format) < 6:
                                errors[episode_path] = 'File with unrecognised resolution: %s %s' % (episode_codec, episode_resolution)
                            else:
                                episodes[episode_path] = {'show': videodir,
                                                          'size': episode_size,
                                                          'codec': episode_codec,
                                                          'height': episode_resolution}
                else:
                    episode_format = episodes[episode_path]['codec'] + '_' + episodes[episode_path]['height']

                # Process shows that have been marked as 'overridden'
                if videodir in codec_override:
                    episodes[episode_path]['codec'] = 'x265'
                    episode_format = episodes[episode_path]['codec'] + '_' + episodes[episode_path]['height']

                # Create a new empty show entry
                if videodir not in shows:
                    shows[videodir] = {'show_size': 0, 'x265_1080p': 0, 'x265_720p': 0, 'x265_sd': 0, 'x264_1080p': 0,
                                       'x264_720p': 0, 'x264_sd': 0, 'mpeg_720p': 0, 'mpeg_sd': 0}

                # Check for valid mediainfo details
                if len(episode_format) < 6:
                    errors[episode_path] = 'Could not obtain video details'
                else:
                    shows[videodir][episode_format] += 1
                    shows[videodir]['show_size'] += episode_size

                # Testing x265 report
                if episodes[episode_path]['codec'] != 'x265':
                    recode += '<tr><td align=center>%s</td><td align=center>%s</td><td align=right>%s</td><td>%s</td></tr>' % (episodes[episode_path]['codec'], episodes[episode_path]['height'], episodes[episode_path]['size'], episode_path)

                # Ensure files have been properly processed
                if episode_path in check_episodes:
                    del check_episodes[episode_path]

    # Update pickle file at the end of each directory
    update_pickle(pickle_file, episodes)
# End of root directory scan
scan_bar.update(episodes_directories)

for episode_path in check_episodes:
    print('\nERROR: File processed previously but currently being skipped: %s' % episode_path)

# Updating HTML report file
with open(report_html, 'w') as report:
    report.write('<html><head><title>TV Shows codec report</title><style> \
table.sortable th:not(.sorttable_sorted):not(.sorttable_sorted_reverse):not(.sorttable_nosort):after { content: " \\25b4\\25be" } \
#shows {font-family: "Trebuchet MS", Arial, Helvetica, sans-serif; border-collapse: collapse; width: 100%; } \
#shows td {border: 1px solid #ddd; padding: 8px; text-align: right} \
#shows td.left {text-align: left} \
#shows td.center {text-align: center} \
#shows th {border: 1px solid #ddd; padding: 8px; text-align: center; padding-top: 12px; padding-bottom: 12px; background-color: #4CAF50; color: white; } \
#shows tr:nth-child(even){background-color: #f2f2f2;} \
#shows tr:hover {background-color: #ddd;}</style> \
<script type="text/javascript" src="sorttable.js"></script></head> \
<body><table class="sortable" id="shows"><tr><th>Show</th><th>Size (MB)</th><th class="sorttable_nosort">Conversion progress</th><th>Ep #</th><th>Qual</th> \
<th>x265 1080p<th>x265 720p</th><th>x265 SD</th><th>x264 1080p</th><th>x264 720p</th><th>x264 SD</th><th>H.262 720p</th><th>H.262 SD</th></tr>')
    total_x265 = 0
    total_episodes = 0
    total_size = 0
    for show, details in sorted(shows.items()):
        x265_episodes = details['x265_1080p'] + details['x265_720p'] + details['x265_sd']
        num_episodes = x265_episodes + details['x264_1080p'] + details['x264_720p'] + details['x264_sd'] + details['mpeg_720p'] + details['mpeg_sd']
        total_x265 += x265_episodes
        total_episodes += num_episodes
        show_size = int(details['show_size'] / 1024 / 1024)
        total_size += show_size
        show_badge = episode_badge(details, num_episodes)
        report.write('<tr><td class="left">%s</td><td>%s</td><td class="center"><progress max="%s" value="%s"> \
            </progress></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td> \
            <td>%s</td><td>%s</td></tr>' % (
            show, show_size, num_episodes, x265_episodes, num_episodes, show_badge, details['x265_1080p'],
            details['x265_720p'], details['x265_sd'], details['x264_1080p'], details['x264_720p'], details['x264_sd'],
            details['mpeg_720p'], details['mpeg_sd']))
    total_stats = 'Scanned %s shows with %s episodes (%s in x265 format - %.2f%%). %.0f GB in total' % (episodes_directories, total_episodes, total_x265, ((total_x265*100)/total_episodes), (total_size/1024))
    report.write('</table><br><table id="shows"><th>%s</th></table></body></html>' % (total_stats))

if len(errors) > 0:
    print('\n\nIssues detected:\n================')
    for messages, values in sorted(errors.items()):
        print('%s - %s' % (messages, values))

with open(recode_html, 'w') as handle_html:
    handle_html.write('<table border=1>%s</table>' % recode)

print('\nFinished full directory scan. %s' % total_stats)
