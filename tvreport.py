#!/usr/bin/env python3
from pymediainfo import MediaInfo
import os, pickle, importlib

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

def update_pickle ( dictionary ):
  with open(pickle_file, 'wb') as handle:
    pickle.dump(dictionary, handle)

# Checking if a scan has been run previously
if os.path.isfile(pickle_file):
  with open(pickle_file, 'rb') as handle:
    episodes = pickle.load(handle)
    # Check if previously scanned files have been deleted
    episodes_pickle = len(episodes)
    print('Found %s episodes from previous scan(s) cached, scanning for removed episodes...' % episodes_pickle)
    scan_bar_progress = 0
    #scan_bar = progressbar.ProgressBar(max_value = episodes_pickle, widgets = [ progressbar.Percentage(), ' (', progressbar.SimpleProgress(), ') ', progressbar.Bar(), ' ', progressbar.Timer(), ' ', progressbar.ETA() ])
    scan_bar = progressbar.ProgressBar(max_value = episodes_pickle)
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

# Processing root directory
episodes_directories = len(next(os.walk(scan_directory))[1])
scan_bar_progress = 0
scan_bar = progressbar.ProgressBar(max_value = episodes_directories)
print('Found %s directories, scanning for episodes...' % episodes_directories)

for dirpath, dirnames, filenames in os.walk(scan_directory, topdown=True):
  scan_bar.update(scan_bar_progress)
  videodir = os.path.basename(dirpath)
  depth = dirpath[len(scan_directory) + len(os.path.sep):].count(os.path.sep)
 
  # Processing show directory
  if depth == 0:
    scan_bar_progress += 1
    #print ('Processing %s...' % videodir, end='\r')
    for video in filenames:
      if video.endswith(tuple(video_extensions)):
        episode_path = os.path.join(dirpath, video)
        episode_size = os.path.getsize(episode_path)
        episode_rescan = 0
        # Check if file has already been scanned previously
        if episode_path in episodes:
          episode_old = episodes.get(episode_path)
          # Check if file size matches previous scan
          if episode_size != episode_old['size']:
            episode_rescan = 1
        # Run mediainfo if file hasn't been scanned previously or has changed
        if episode_rescan == 1 or not episode_path in episodes:
          videoinfo = MediaInfo.parse(episode_path)
          episode_codec = ''
          episode_height = ''
          for track in videoinfo.tracks:
            if track.track_type == 'Video':
              if track.format == 'HEVC':
                episode_codec = 'x265'
              elif track.format == 'AVC':
                episode_codec = 'x264'
              elif track.format == 'MPEG-4 Visual':
                episode_codec = 'avi'

              if track.height >= 800:
                episode_height = '1080p'
              elif track.height >= 640 and track.height < 800:
                episode_height = '720p'
              elif track.height < 640:
                episode_height = 'sd'

              # Codec and/or height size does not match the criteria above
              if episode_codec == '' or episode_height == '':
                print ('Warning: File with unrecognised resolution %s: %s %s' % (episode_path, track.format, track.height))
              else:
                episodes[episode_path] = {'show': videodir,
                                          'size': episode_size,
                                          'codec': episode_codec,
                                          'height': episode_height}
    # Update pickle file at the end of each directory
    update_pickle(episodes)
# End of root directory scan
scan_bar.update(episodes_directories)

# Creating show report
for key, values in episodes.items():
  show_name = values['show']
  if show_name not in shows:
    shows[show_name] = { 'x265_1080p': 0, 'x265_720p': 0, 'x265_sd': 0, 'x264_1080p': 0, 'x264_720p': 0, 'x264_sd': 0, 'avi_720p': 0, 'avi_sd': 0 }
  episode_format = values['codec'] + '_' + values['height']
  shows[show_name][episode_format] += 1
  if 'show_size' in shows[show_name]:
    shows[show_name]['show_size'] += values['size']
  else:
    shows[show_name]['show_size'] = values['size']

# Updating HTML report file
with open(html_file, 'w') as handle:
  handle.write('<html><head><title>TV Shows codec report</title><style> \
table.sortable th:not(.sorttable_sorted):not(.sorttable_sorted_reverse):not(.sorttable_nosort):after { content: " \\25b4\\25be" } \
#shows {font-family: "Trebuchet MS", Arial, Helvetica, sans-serif; border-collapse: collapse; width: 100%; } \
#shows td {border: 1px solid #ddd; padding: 8px; text-align: right} \
#shows td.left {text-align: left} \
#shows td.center {text-align: center} \
#shows th {border: 1px solid #ddd; padding: 8px; text-align: center; padding-top: 12px; padding-bottom: 12px; background-color: #4CAF50; color: white; } \
#shows tr:nth-child(even){background-color: #f2f2f2;} \
#shows tr:hover {background-color: #ddd;}</style> \
<script type="text/javascript" src="sorttable.js"></script></head> \
<body><table class="sortable" id="shows"><tr><th>Show</th><th>Size (MB)</th><th class="sorttable_nosort">Conversion progress</th><th>Episodes</th> \
<th>x265 1080p<th>x265 720p</th><th>x265 SD</th><th>x264 1080p</th><th>x264 720p</th><th>x264 SD</th><th>H.263 720p</th><th>H.263 SD</th></tr>')
  total_x265 = 0
  total_episodes = 0
  total_size = 0
  for show, details in sorted(shows.items()):
    x265_episodes = details['x265_1080p'] + details['x265_720p'] + details['x265_sd']
    num_episodes = x265_episodes + details['x264_1080p'] + details['x264_720p'] + details['x264_sd'] + details['avi_720p'] + details['avi_sd']
    total_x265 += x265_episodes
    total_episodes += num_episodes
    show_size = int(details['show_size'] / 1024 / 1024)
    total_size += show_size
    handle.write('<tr><td class="left">%s</td><td>%s</td><td class="center"><progress max="%s" value="%s"></progress></td><td>%s</td>' % (show, show_size, num_episodes, x265_episodes, num_episodes))
    handle.write('<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (details['x265_1080p'], details['x265_720p'], details['x265_sd'], details['x264_1080p'], details['x264_720p'], details['x264_sd'], details['avi_720p'], details['avi_sd']))
  handle.write('</table><br><table id="shows"><th>Scanned %s shows with %s episodes, out of which %s are in x265 format. %s GB in total</th></table></body></html>' % (episodes_directories, total_episodes, total_x265, int(total_size/1024)))

print('\nFinished full directory scan. %s episodes (%s in x265 format), %s GB in total.' % (total_episodes, total_x265, int(total_size/1024)))
