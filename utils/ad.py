import re
from collections import namedtuple

import binascii
from urllib.parse import ParseResult

from django.utils.http import urlsafe_base64_decode, _urlparse

from utils.http import urlparse_qs_or_fragment, find_params

UTM = namedtuple('UTM', ('utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'))


def parse_url_utms(url):
    """
    :param url:
    :return: UTM

    >>> parse_url_utms('http://www.example.org/path?utm_source=source&utm_medium=medium&utm_campaign=camp1&utm_term=boats&utm_content=boats+boats+boats')
    UTM(utm_source='source', utm_medium='medium', utm_campaign='camp1', utm_term='boats', utm_content='boats boats boats')
    >>> parse_url_utms('http://www.example.org/path#utm_source=source&utm_medium=medium&utm_campaign=camp1&utm_term=boats&utm_content=boats+boats+boats')
    UTM(utm_source='source', utm_medium='medium', utm_campaign='camp1', utm_term='boats', utm_content='boats boats boats')
    >>> parse_url_utms('http://www.example.org/path?utm_source=source&utm_medium=medium&utm_campaign=camp1&utm_term=boats&utm_content=boats+boats+boats#utm_source=f&utm_medium=f&utm_campaign=f&utm_term=f&utm_content=f')
    UTM(utm_source='source', utm_medium='medium', utm_campaign='camp1', utm_term='boats', utm_content='boats boats boats')
    >>> parse_url_utms('http://www.example.org/path?utm_source=source&utm_medium=medium&utm_campaign=camp1&utm_term=boats&utm_content=boats+boats+boats#utm_medium=f&utm_campaign=f&utm_term=f&utm_content=f')
    UTM(utm_source='source', utm_medium='medium', utm_campaign='camp1', utm_term='boats', utm_content='boats boats boats')
    >>> parse_url_utms('http://www.example.org/path?utm_medium=medium&utm_campaign=camp1&utm_term=boats&utm_content=boats+boats+boats')

    >>> parse_url_utms('http://www.example.org/path?utm_medium=medium&utm_campaign=camp1&utm_term=boats&utm_content=boats+boats+boats#utm_source=f')

    """
    params = urlparse_qs_or_fragment(
        url, ('utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content')
    )
    utm_source = params.get('utm_source', '')
    if not utm_source:
        return None
    return UTM(
        utm_source, params.get('utm_medium', ''), params.get('utm_campaign', ''),
        params.get('utm_term', ''), params.get('utm_content', '')
    )


Openstat = namedtuple('Openstat', ('service', 'campaign', 'ad', 'source'))


def parse_url_openstat(url):
    """
    Parse openstat label and return Openstat namedtuple
    http://wiki.openstat.ru/Openstat/OpenstatMarker
    @todo: test this http://www.example.org/path?query#_openstat_openstat=openstat.ru;camp1;ad1234;top-left-corner must return ('openstat.ru', 'camp1', 'ad1234', 'top-left-corner')
    @todo: test http://www.example.org/path?_openstat=openstat.ru;camp%1B;ad1234;top-left-corner must return None
    :param url: url
    :type url: str
    :return: Openstat namedtuple or None
    :rtype Openstat
    >>> parse_url_openstat('http://www.example.org/path?_openstat=openstat.ru;camp1;ad1234;top-left-corner')
    Openstat(service='openstat.ru', campaign='camp1', ad='ad1234', source='top-left-corner')
    >>> parse_url_openstat('http://www.example.org/path?key1=value1&key2=value2&_openstat=openstat.ru;camp1;ad1234;top-left-corner')
    Openstat(service='openstat.ru', campaign='camp1', ad='ad1234', source='top-left-corner')
    >>> parse_url_openstat('http://www.example.org/path?key1=value1&_openstat=openstat.ru;camp1;ad1234;top-left-corner&key2=value2')
    Openstat(service='openstat.ru', campaign='camp1', ad='ad1234', source='top-left-corner')
    >>> parse_url_openstat('http://www.example.org/path?_openstat=openstat.ru;;;')
    Openstat(service='openstat.ru', campaign='', ad='', source='')
    >>> parse_url_openstat('http://www.example.org/path?_openstat=b3BlbnN0YXQucnU7Y2FtcDE7YWQxMjM0O3RvcC1sZWZ0LWNvcm5lcg')
    Openstat(service='openstat.ru', campaign='camp1', ad='ad1234', source='top-left-corner')
    >>> parse_url_openstat('http://www.example.org/path?_openstat=openstat.ru;camp%201;ad%201234;top%20left%20corner')
    Openstat(service='openstat.ru', campaign='camp 1', ad='ad 1234', source='top left corner')
    >>> parse_url_openstat('http://www.example.org/path?_openstat=%D0%BE%D0%BF%D0%B5%D0%BD%D1%81%D1%82%D0%B0%D1%82.%D1%80%D1%84;1;ad%203;%D0%B2%D0%B5%D1%80%D1%85')
    Openstat(service='опенстат.рф', campaign='1', ad='ad 3', source='верх')
    >>> parse_url_openstat('http://www.example.org/path?_openstat=0L7Qv9C10L3RgdGC0LDRgi7RgNGEOzE7YWQgMzvQstC10YDRhQ')
    Openstat(service='опенстат.рф', campaign='1', ad='ad 3', source='верх')
    >>> parse_url_openstat('http://www.example.org/path?query#_openstat=openstat.ru;camp1;ad1234;top-left-corner')
    Openstat(service='openstat.ru', campaign='camp1', ad='ad1234', source='top-left-corner')
    >>> parse_url_openstat('http://www.example.org/path#_openstat=openstat.ru;camp1;ad1234;top-left-corner')
    Openstat(service='openstat.ru', campaign='camp1', ad='ad1234', source='top-left-corner')
    >>> parse_url_openstat('http://www.example.org/path?_openstt=openstat.ru;camp1;ad1234;top-left-corner')

    >>> parse_url_openstat('http://www.example.org/path?_openstat;camp1;ad1234;top-left-corner=')

    """
    params = urlparse_qs_or_fragment(url, ('_openstat',))
    if '_openstat' not in params:
        return None
    label_encoded = params['_openstat']
    if ';' in label_encoded:
        label = label_encoded
    else:
        try:
            label = urlsafe_base64_decode(label_encoded).decode('UTF-8')
        except (binascii.Error, ValueError, UnicodeDecodeError):
            return None
    try:
        service, campaign, ad, source = label.split(';')
    except ValueError:
        return None
    return Openstat(service, campaign, ad, source)


def parse_traffic_channel(referrer, url):
    """

    :param referrer:
    :param url:
    :return:
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=111&utm_medium=asd-display', 'https://landing-domain.com/')
    'display'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=asd-dvigus', 'https://landing-domain.com/')
    'display'
    >>> parse_traffic_channel('https://ref-page.com/img1.begun', 'https://landing-domain.com/')
    'display'
    >>> parse_traffic_channel('https://ref-page.com/?_openstat=B2BContext;;;', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=avitopromo', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=111&utm_medium=paidsearch', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?ymclid=123', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?_openstat=market.yandex.ru;;;', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://m.market.yandex.ru/', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=111&utm_medium=aport', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=aport', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?_openstat=begun;;;', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://podarki.begun.ru/', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/click123dd.begun', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?gclid=123', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://googleadservices.com/', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?cm_id=Google+AdWords', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?yclid=123', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?cm_id=Яндекс.Директ', 'https://landing-domain.com/')
    'paid'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=advertise-qq', 'https://landing-domain.com/')
    'affiliate'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=123&utm_medium=affiliate-qq', 'https://landing-domain.com/')
    'affiliate'
    >>> parse_traffic_channel('https://ref-advertise-page.com/', 'https://landing-domain.com/')
    'affiliate'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=youtube-qq', 'https://landing-domain.com/')
    'social'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=smm-qq', 'https://landing-domain.com/')
    'referral'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=smm', 'https://landing-domain.com/')
    'social'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=123&utm_medium=reddit-qq', 'https://landing-domain.com/')
    'social'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=123&utm_medium=ask.fm', 'https://landing-domain.com/')
    'social'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=123&utm_medium=ask.fmqq', 'https://landing-domain.com/')
    'referral'
    >>> parse_traffic_channel('https://ref-tumblr-page.com/', 'https://landing-domain.com/')
    'social'
    >>> parse_traffic_channel('https://vk.com/', 'https://landing-domain.com/')
    'social'
    >>> parse_traffic_channel('https://vvk.com/', 'https://landing-domain.com/')
    'referral'
    >>> parse_traffic_channel('https://m.ok.ru/', 'https://landing-domain.com/')
    'social'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=email', 'https://landing-domain.com/')
    'email'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=e-mail', 'https://landing-domain.com/')
    'email'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=123&utm_medium=emailq', 'https://landing-domain.com/')
    'email'
    >>> parse_traffic_channel('https://ref-page.com/?utm_source=123&utm_medium=e-mailq', 'https://landing-domain.com/')
    'email'
    >>> parse_traffic_channel('https://ref-page.com/?_openstat=email;;;', 'https://landing-domain.com/')
    'email'
    >>> parse_traffic_channel('https://ref-page.com/?_openstat=e-mail;;;', 'https://landing-domain.com/')
    'email'
    >>> parse_traffic_channel('https://ref-page.com/?from=e-mail11', 'https://landing-domain.com/')
    'email'
    >>> parse_traffic_channel('https://ref-page.com/?from=email111', 'https://landing-domain.com/')
    'email'
    >>> parse_traffic_channel('https://rambler.ru/', 'https://landing-domain.com/')
    'organic'
    >>> parse_traffic_channel('https://mail.ru/', 'https://landing-domain.com/')
    'organic'
    >>> parse_traffic_channel('https://yahoo.com/', 'https://landing-domain.com/')
    'organic'
    >>> parse_traffic_channel('https://ask.com/', 'https://landing-domain.com/')
    'organic'
    >>> parse_traffic_channel(None, 'https://landing-domain.com/')
    'direct'
    >>> parse_traffic_channel('', 'https://landing-domain.com/')
    'direct'
    >>> parse_traffic_channel('', '')
    'direct'
    >>> parse_traffic_channel('https://landing-domain.com/', 'https://landing-domain.com/')
    'internal'
    >>> parse_traffic_channel('https://ref-page.com/', 'https://landing-domain.com/')
    'referral'
    """
    if referrer is None:
        return 'direct'
    parsed = _urlparse(referrer)
    parsed_url = _urlparse(url)
    channel = None
    utms = parse_url_utms(referrer)
    openstat = parse_url_openstat(referrer)
    if _is_display(referrer, utms):
        channel = 'display'
    elif _is_paid(referrer, parsed, utms, openstat):
        channel = 'paid'
    elif _is_affiliate(parsed, utms):
        channel = 'affiliate'
    elif _is_social(parsed, utms):
        channel = 'social'
    elif _is_email(parsed, utms, openstat):
        channel = 'email'
    elif _is_organic(parsed):
        channel = 'organic'
    elif _is_direct(referrer):
        channel = 'direct'
    elif _is_internal(parsed, parsed_url):
        channel = 'internal'
    else:
        channel = 'referral'
    return channel


def _is_display(url: str, utms: UTM):
    if utms and any(w in utms.utm_medium.lower() for w in (
        'display', 'cpm', 'banner', 'tgb', 'banners.adfox.ru'
    )):
        return True
    elif utms and  any(w in utms.utm_source.lower() for w in (
        'criteo', 'dvigus', 'adriver', 'advmaker'
    )):
        return True
    elif re.search(r'img\d{1,}\.begun', url):
        return True
    else:
        return False


def _is_paid(url: str, parsed: ParseResult, utms: UTM, openstat: Openstat):
    if openstat and any(w in openstat.service for w in ('B2BContext', )):
        return True
    elif utms and any(w in utms.utm_source.lower() for w in (
        'elama', 'content.adfox.ru', 'avitopromo',
        'avitocontext', 'kavanga', 'marketgid', 'merchant'
    )):
        return True
    elif utms and any(w in utms.utm_medium.lower() for w in (
        'cpc', 'ppc', 'paidsearch', 'cpv', 'cpp', 'content-text', 'cps', 'pps'
    )):
        return True
    elif _is_paid_yandex_market(parsed, openstat):
        return True
    elif _is_paid_aport(utms):
        return True
    elif _is_paid_begun(url, parsed, openstat):
        return True
    elif _is_paid_google_adwords(parsed):
        return True
    elif _is_paid_yandex_direct(parsed, openstat):
        return True
    else:
        return False


def _is_paid_yandex_market(parsed: ParseResult, openstat: Openstat):
    if find_params(parsed.query, ('ymclid',)).get('ymclid'):
        return True
    elif openstat and openstat.service == 'market.yandex.ru':
        return True
    elif parsed.hostname in ('market.yandex.ru', 'm.market.yandex.ru'):
        return True
    else:
        return False


def _is_paid_aport(utms: UTM):
    if utms and any(w in utms.utm_medium.lower() for w in ('aport',)):
        return True
    elif utms and any(w in utms.utm_source.lower() for w in ('aport',)):
        return True
    else:
        return False


def _is_paid_begun(url: str, parsed: ParseResult, openstat: Openstat):
    if openstat and any(w in openstat.service for w in ('begun',)):
        return True
    elif parsed.hostname in ('rmt.begun.ru', 'podarki.begun.ru'):
        return True
    elif re.search(r'click[^\.]+\.begun', url):
        return True
    else:
        return False


def _is_paid_google_adwords(parsed: ParseResult):
    ga = find_params(parsed.query, ('gclid', 'cm_id'))
    if ga.get('gclid'):
        return True
    elif parsed.hostname == 'googleadservices.com':
        return True
    elif ga.get('cm_id') == 'Google AdWords':
        return True
    else:
        return False


def _is_paid_yandex_direct(parsed: ParseResult, openstat: Openstat):
    yd = find_params(parsed.query, ('yclid', 'cm_id'))
    if openstat and openstat.service == 'direct.yandex.ru':
        return True
    elif yd.get('yclid'):
        return True
    elif parsed.hostname and 'yabs.yandex.ru' in parsed.hostname:
        return True
    elif yd.get('cm_id') == 'Яндекс.Директ':
        return True
    else:
        return False


def _is_affiliate(parsed: ParseResult, utms: UTM):
    if utms and any(w in utms.utm_source.lower() for w in (
        'advertise', 'actionpay', 'kredov', 'admitad', 'gdeslon',
        'cityads', 'qxplus', 'leadgidru', 'doubletrade', 'salesdoubler',
        'leadssu', 'elonleads', 'adwad', 'tradetracker', 'afrek', 'sellaction'
    )):
        return True
    elif utms and any(w in utms.utm_medium.lower() for w in (
        'affiliate', 'cpa', 'cpo', 'cpl'
    )):
        return True
    elif parsed.hostname and any(w in parsed.hostname.lower() for w in (
        'advertise', 'actionpay', 'kredov', 'admitad', 'gdeslon',
        'cityads', 'leadgid.ru', 'doubletrade', 'salesdoubler', 'leadssu',
        'elonleads', 'adwad', 'tradetracker', 'afrek', '7offers',
        'zorkanetwork.com', 'adpro.ru', 'actionads', 'lead-r'
    )):
        return True
    else:
        return False


def _is_social(parsed: ParseResult, utms: UTM):
    if utms and any(w in utms.utm_source.lower() for w in (
        'youtube', 'vkontakte', 'facebook', 'instagram', 'twitter',
        'mytarget', 'viber', 'linkedin', 'livejournal', 'odnoklassniki',
        'plus.google.com', 'googleplus', 'my.mail.ru', 'mirtesen.ru',
        'delicious', 'tumblr', 'pinterest', 'reddit', 'stumbleupon'
    )):
        return True
    elif utms and utms.utm_source.lower() in (
        'smm', 'vk', 'vk.com', 'fb', 'ask.fm', 'ok.ru', 'ok'
    ):
        return True
    elif utms and any(w in utms.utm_medium.lower() for w in (
        'youtube', 'vkontakte', 'facebook', 'instagram', 'twitter',
        'mytarget', 'viber', 'linkedin', 'livejournal', 'odnoklassniki',
        'plus.google.com', 'googleplus', 'my.mail.ru', 'mirtesen.ru',
        'delicious', 'tumblr', 'pinterest', 'reddit', 'stumbleupon'
    )):
        return True
    elif utms and utms.utm_medium.lower() in (
        'smm', 'vk', 'vk.com', 'fb', 'ask.fm', 'ok.ru', 'ok'
    ):
        return True
    elif parsed.hostname and any(w in parsed.hostname.lower() for w in (
        'youtube', 'facebook', 'instagram', 'livejournal', 'pinterest',
        'soundcloud', 'tagged', 'tumblr', 'twitter', 'linkedin',
        'plus.google.com', 'my.mail.ru', 'mirtesen.ru', 'reddit'
    )):
        return True
    elif parsed.hostname and parsed.hostname.lower() in  (
        'ask.fm', 'last.fm', 'vk.com'
    ):
        return True
    elif parsed.hostname and any(re.search(r, parsed.hostname.lower()) for r in (
        r'^ok\.ru' , r'^m\.ok\.ru'
    )):
        return True
    else:
        return False


def _is_email(parsed: ParseResult, utms: UTM, openstat: Openstat):
    from_arg = find_params(parsed.query, ('from',)).get('from', '')
    if utms and any(w in utms.utm_source.lower() for w in (
        'email', 'e-mail'
    )):
        return True
    elif utms and any(w in utms.utm_medium.lower() for w in (
        'email', 'e-mail'
    )):
        return True
    elif openstat and any(w in openstat.service.lower() for w in (
        'email', 'e-mail'
    )):
        return True
    elif any(w in from_arg.lower() for w in (
        'email', 'e-mail'
    )):
        return True
    else:
        return False


def _is_organic(parsed: ParseResult):
    if parsed.hostname and any(w in parsed.hostname.lower() for w in (
        'rambler', 'bing', 'mail.ru', 'yahoo', 'nigma', 'ask.com', 'yandex', 'google'
    )):
        return True
    else:
        return False


def _is_direct(url: str):
    return url is None or url == ''


def _is_internal(parsed_referrer: ParseResult, parsed_url: ParseResult):
    return parsed_referrer.hostname == parsed_url.hostname

# 
# def _is_referral(url: str):
#     return url is not None and url != ''
