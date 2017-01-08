#!/usr/bin/env python3
from pymediainfo import MediaInfo
import os
import pickle
import importlib

if not importlib.util.find_spec('progressbar'):
    print('Error: Python module not found. Install progressbar2.')
    exit(1)
else:
    import progressbar

config_file = os.path.expanduser('~') + '/.tvreport'
# Check configuration file
if not os.path.isfile(config_file):
    print('Error: Config file %s missing. Copy tvreport.cfg to %s and configure as required.' % (config_file, config_file))
else:
    exec(compile(open(config_file, "rb").read(), config_file, 'exec'))

if not os.path.isdir(scan_directory):
    print('Error: %s is not a directory or doesn\'t exist. Check your %s config file.' % (scan_directory, config_file))
    exit(1)


def update_pickle(dictionary):
    with open(pickle_file, 'wb') as handle:
        pickle.dump(dictionary, handle)


def track_codec(track):
    if track.format == 'HEVC':
        return 'x265'
    elif track.format == 'AVC':
        return 'x264'
    elif track.format == 'MPEG-4 Visual' or track.format == 'MPEG Video':
        return 'mpeg'
    else:
        return ''


def track_resolution(track):
    if track.height >= 800:
        return '1080p'
    elif track.height >= 640 and track.height < 800:
        return '720p'
    elif track.height < 640:
        return 'sd'
    else:
        return ''

# Checking if a scan has been run previously
if os.path.isfile(pickle_file):
    with open(pickle_file, 'rb') as handle:
        episodes = pickle.load(handle)
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
    update_pickle(episodes)
else:
    episodes = dict()
shows = dict()
errors = dict()

# Processing root directory
episodes_directories = len(next(os.walk(scan_directory))[1])
scan_bar_progress = 0
scan_bar = progressbar.ProgressBar(max_value=episodes_directories)
print('Found %s directories, scanning for episodes...' % episodes_directories)

recode = ''

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

                # Check if file has already been scanned previously
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
                    # or no episode_path in episodes:
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

                if videodir not in shows:
                    shows[videodir] = {'show_size': 0, 'x265_1080p': 0, 'x265_720p': 0, 'x265_sd': 0, 'x264_1080p': 0, 'x264_720p': 0, 'x264_sd': 0, 'mpeg_720p': 0, 'mpeg_sd': 0}

                if len(episode_format) < 6:
                    errors[episode_path] = 'Could not obtain video details'
                else:
                    shows[videodir][episode_format] += 1
                    shows[videodir]['show_size'] += episode_size

                # Testing x265 report
                if episodes[episode_path]['codec'] != 'x265':
                    recode += '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (episodes[episode_path]['codec'], episodes[episode_path]['height'], episode_path)

    # Update pickle file at the end of each directory
    update_pickle(episodes)
# End of root directory scan
scan_bar.update(episodes_directories)

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
        if (details['x265_1080p'] + details['x264_1080p']) == num_episodes:
            show_badge = '1080p'
        elif (details['x265_720p'] + details['x264_720p'] + details['mpeg_720p']) == num_episodes:
            show_badge = '720p'
        elif (details['x265_sd'] + details['x264_sd'] + details['mpeg_sd']) == num_episodes:
            show_badge = 'SD'
        else:
            show_badge = 'Mix'
        report.write('<tr><td class="left">%s</td><td>%s</td><td class="center"><progress max="%s" value="%s"></progress></td><td>%s</td><td>%s</td>' % (show, show_size, num_episodes, x265_episodes, num_episodes, show_badge))
        report.write('<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (details['x265_1080p'], details['x265_720p'], details['x265_sd'], details['x264_1080p'], details['x264_720p'], details['x264_sd'], details['mpeg_720p'], details['mpeg_sd']))
    total_stats = 'Scanned %s shows with %s episodes (%s in x265 format - %.2f%%). %.0f GB in total' % (episodes_directories, total_episodes, total_x265, ((total_x265*100)/total_episodes), (total_size/1024))
    report.write('</table><br><table id="shows"><th>%s</th></table></body></html>' % (total_stats))

if len(errors) > 0:
    print('\n\nIssues detected:\n================')
    for messages, values in sorted(errors.items()):
        print('%s - %s' % (messages, values))

with open(recode_html, 'w') as handle:
    handle.write('<table border=1>%s</table>' % (recode))

print('\nFinished full directory scan. %s' % total_stats)
