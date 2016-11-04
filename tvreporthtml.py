from report_output import shows
import pprint

print('<html><body><table border=1><tr><th rowspan=2>Show</th><th rowspan=2>Conversion progress</th><th rowspan=2>Episodes</th><th colspan=3>x265</th><th colspan=3>x264<th rowspan=2>MPEG-4 SD</th></tr>')
print('<tr><th>1080p</th><th>720p</th><th>SD</th><th>1080p</th><th>720p</th><th>SD</th></tr>')
for show, details in sorted(shows.items()):
    #pprint.pprint(details)
    #print(details['x265_1080p'])
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
    print('<tr><td>%s</td><td><progress max="%s" value="%s"></progress></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (show, num_episodes, x265_episodes, num_episodes, x265_1080p, x265_720p, x265_sd, x264_1080p, x264_720p, x264_sd, avi_sd))

print('</table></body></html>')
#pprint.pprint(shows)
