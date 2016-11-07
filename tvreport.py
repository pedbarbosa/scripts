#!/user/bin/env python3
from pymediainfo import MediaInfo
import os, pickle, pprint

# Environment settings
if os.name == 'nt':
  scan_directory = 'D:\\Video\\TV'
else:
  scan_directory = '/storage/x265'
pickle_file = '.tvreport.pickle'
html_file = 'D:\\Video\\TV\\tvreport.html'

def update_pickle ( dictionary ):
  with open(pickle_file, 'wb') as handle:
    pickle.dump(dictionary, handle)
  handle.close

# Checking if a scan has been run previously
if os.path.isfile(pickle_file):
  with open(pickle_file, 'rb') as handle:
    episodes = pickle.load(handle)
    handle.close
    # Check if previously scanned files have been deleted
    for episode_path in list(episodes):
      if not os.path.exists(episode_path):
        del episodes[episode_path]
  update_pickle(episodes)
else:
  episodes = dict()
shows = dict()

# Processing root directory
for dirpath, dirnames, filenames in os.walk(scan_directory):
  videodir=os.path.basename(dirpath)

  # Processing show directory
  for video in filenames:
    if video.endswith('.mkv') or video.endswith('.mp4') or video.endswith('.avi'):
      episode_path = os.path.join(dirpath, video)
      episode_size = os.path.getsize(episode_path)
      episode_rescan = 0
      episode_codec = ''
      episode_height = ''
      # Check if file has already been scanned previously
      if episode_path in episodes:
        episode_old = episodes.get(episode_path)
        # Check if file size matches previous scan
        if episode_size != episode_old['size']:
          episode_rescan = 1
      # Run mediainfo if file hasn't been scanned previously or has changed
      if episode_rescan == 1 or not episode_path in episodes:
        videoinfo = MediaInfo.parse(episode_path)
        for track in videoinfo.tracks:
          if track.track_type == 'Video':
            if track.format == 'HEVC':
              episode_codec = 'x265'
            elif track.format == 'AVC':
              episode_codec = 'x264'
            elif track.format == 'MPEG-4 Visual':
              episode_codec = 'avi'

            if track.height >= 960:
              episode_height = '1080p'
            elif track.height >= 700 and track.height <= 722:
              episode_height = '720p'
            elif track.height <= 480:
              episode_height = 'sd'

            # Codec and/or height size does not match the criteria above
            if episode_codec == '' or episode_height == '':
              print ('File with unrecognised resolution %s: %s %s' % (episode_path, track.format, track.height))
            else:
              episodes[episode_path] = {'show': videodir,
                                        'size': episode_size,
                                        'codec': episode_codec,
                                        'height': episode_height}
  # End of show directory
  print('Finished processing %s...' % videodir)
  # Update pickle file at the end of each directory
  update_pickle(episodes)
# End of root directory scan

# Creating show report
for key, values in episodes.items():
  show_name = values['show']
  if show_name not in shows:
    shows[show_name]=dict()
  episode_format = values['codec'] + '_' + values['height']
  if episode_format in shows[show_name]:
    shows[show_name][episode_format] += 1
  else:
    shows[show_name][episode_format] = 1
  if 'show_size' in shows[show_name]:
    shows[show_name]['show_size'] += values['size']
  else:
    shows[show_name]['show_size'] = values['size']

# Updating HTML report file
with open(html_file, 'w') as handle:
  handle.write('<html><body><table border=1><tr><th rowspan=2>Show</th><th rowspan=2>Size</th><th rowspan=2>Conversion progress</th><th rowspan=2>Episodes</th><th colspan=3>x265</th><th colspan=3>x264<th rowspan=2>MPEG-4 SD</th></tr>')
  handle.write('<tr><th>1080p</th><th>720p</th><th>SD</th><th>1080p</th><th>720p</th><th>SD</th></tr>')
  for show, details in sorted(shows.items()):
    if 'x265_1080p' in details:
        x265_1080p = details['x265_1080p']
    else:
        x265_1080p = 0
    if 'x265_720p' in details:
        x265_720p = details['x265_720p']
    else:
        x265_720p = 0
    if 'x265_sd' in details:
        x265_sd = details['x265_sd']
    else:
        x265_sd = 0
    if 'x264_1080p' in details:
        x264_1080p = details['x264_1080p']
    else:
        x264_1080p = 0
    if 'x264_720p' in details:
        x264_720p = details['x264_720p']
    else:
        x264_720p = 0
    if 'x264_sd' in details:
        x264_sd = details['x264_sd']
    else:
        x264_sd = 0
    if 'avi_sd' in details:
        avi_sd = details['avi_sd']
    else:
        avi_sd = 0
    x265_episodes = x265_1080p + x265_720p + x265_sd
    num_episodes = x265_episodes + x264_1080p + x264_720p + x264_sd + avi_sd
    show_size = int(details['show_size'] / 1024 / 1024)
    handle.write('<tr><td>%s</td><td>%s MB</td><td><progress max="%s" value="%s"></progress></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (show, show_size, num_episodes, x265_episodes, num_episodes, x265_1080p, x265_720p, x265_sd, x264_1080p, x264_720p, x264_sd, avi_sd))
  handle.write('</table></body></html>')
  handle.close
