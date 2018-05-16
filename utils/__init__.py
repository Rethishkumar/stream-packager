import os
import re
import iso8601
import logger
from time import strftime

LOG = logger.get_logger(__name__)

os.environ['TZ'] = 'UTC'


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


def cast_to_time(value):
    return iso8601.parse_date(value)


def format_time(value):
    return strftime('%Y-%m-%dT%H:%M:%SZ')


def delete_file(filename):
    os.remove(filename)


def cast_to_duration(seconds):
    return 'PT%dS' % (seconds)


def extract_segment_number(segment_url):

    PATTERN = '.*?(?P<segment_number>[\d]+)\.(m4s|ts)'
    m = re.match(PATTERN, segment_url)
    if m is None:
        LOG.warning('invalid segment_url %s', segment_url)
        raise KeyError('invalid segment_url %s', segment_url)
    return m.group('segment_number')



# def cast_to_duration(date_time):
#     return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime(epoch))

# def datetime_to_epoch(date_time):

#     # convert values such as 2018-05-02T04:53:24 to epoch
#     os.environ['TZ'] = 'UTC'

#     time_formats = [
#         '%Y-%m-%dT%H:%M:%S.%fZ',  # with micro seconds
#         '%Y-%m-%dT%H:%M:%SZ',
#     ]

#     for time_format in time_formats:
#         LOG.debug('date_time %s time_format %s', date_time, time_format)
#         try:
#             retval = int(time.mktime(time.strptime(date_time, time_format)))
#         except ValueError:
#             continue
#     return retval


# def epoch_to_datetime(epoch):
#     return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime(epoch))
