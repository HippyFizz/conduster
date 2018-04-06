from datetime import datetime
from django.utils import timezone


def fromtimestamp_ms(ms):
    '''
    :param ms {int}: milliseconds in utc
    :return {datetime}: timezone aware datetime
    '''
    return timezone.make_aware(
        datetime.utcfromtimestamp(ms//1000).replace(microsecond=ms%1000*1000)
    )


def fromtimestamp(s):
    '''
    :param s {float}: seconds in utc
    :return {datetime}: timezone aware datetime
    '''
    return timezone.make_aware(datetime.utcfromtimestamp(s))


def strptime(date_str: str, format_str: str = '%Y-%m-%d'):
    return timezone.make_aware(datetime.strptime(date_str, format_str))
