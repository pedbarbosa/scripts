from pymediainfo import MediaInfo
import os

import pprint
counter=0

shows=dict()

for dirpath, dirnames, filenames in os.walk('D:\\Video\\TV'):
    videodir=os.path.basename(dirpath)

    for video in filenames:
        if video.endswith('.mkv') or video.endswith('.mp4') or video.endswith('.avi'):
            videoinfo = MediaInfo.parse(os.path.join(dirpath, video))
            for track in videoinfo.tracks:
                if track.track_type == 'Video':
                    counter+=1
                    if videodir not in shows:
                        shows[videodir]=dict()
                    if track.format == 'HEVC':
                        if track.height >= 960:
                            if 'x265_1080p' in shows[videodir]:
                                shows[videodir]['x265_1080p'] += 1
                            else:
                                shows[videodir]['x265_1080p'] = 1
                        elif track.height > 700 and track.height <= 722:
                            if 'x265_720p' in shows[videodir]:
                                shows[videodir]['x265_720p'] += 1
                            else:
                                shows[videodir]['x265_720p'] = 1
                        elif track.height < 600:
                            if 'x265_sd' in shows[videodir]:
                                shows[videodir]['x265_sd'] += 1
                            else:
                                shows[videodir]['x265_sd'] = 1
                        else:
                            print('HEVC file with unrecognised resolution %s: %s %s' % (os.path.join(dirpath,video), track.format, track.height))
                    elif track.format == 'AVC':
                        if track.height >= 960:
                            if 'x264_1080p' in shows[videodir]:
                                shows[videodir]['x264_1080p'] += 1
                            else:
                                shows[videodir]['x264_1080p'] = 1
                        elif track.height > 700 and track.height <= 722:
                            if 'x264_720p' in shows[videodir]:
                                shows[videodir]['x264_720p'] += 1
                            else:
                                shows[videodir]['x264_720p'] = 1
                        elif track.height < 600:
                            if 'x264_sd' in shows[videodir]:
                                shows[videodir]['x264_sd'] += 1
                            else:
                                shows[videodir]['x264_sd'] = 1
                        else:
                            print('AVC file with unrecognised resolution %s: %s %s' % (os.path.join(dirpath,video), track.format, track.height))
                    elif track.format == 'MPEG-4 Visual':
                            if 'avi_sd' in shows[videodir]:
                                shows[videodir]['avi_sd'] += 1
                            else:
                                shows[videodir]['avi_sd'] = 1
                    else:
                        print('Unhandled video format found on %s: %s %s' % (os.path.join(dirpath,video), track.format, track.height))
            
    print('Finished processing %s...' % videodir)
    #if videodir in shows:
    #    pprint.pprint(shows)
pprint.pprint(shows)

