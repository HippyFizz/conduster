# -*- coding: utf-8 -*-

def get_os_group_by_family(family: str):
    family = family.lower()
    if 'windows' in family:
        return 'Windows'
    elif 'android' in family:
        return 'Google Android'
    elif any(w in family for w in ('ios', 'iphone')):
        return 'iOS'
    elif any(w in family for w in ('macos', 'mac os', 'apple', 'darwin')):
        return 'Mac OS'
    elif any(w in family for w in ('tizen',)):
        return 'Tizen'
    elif any(w in family for w in ('chrome os', 'chromeos', 'chromiumos', 'chromium os')):
        return 'Google Chrome OS'
    elif any(w in family for w in ('blackberry os', 'blackberry', 'rim')):
        return 'BlackBerry OS'
    elif any(w in family for w in ('symbianos', 'symbian os', 'uiq', 'series', 'moap')):
        return 'SymbianOS'
    elif any(w in family for w in ('bsd', 'демос', 'ultrix', 'trueos')):
        return 'BSD'
    elif any(w in family for w in ('linux', 'mint', 'ubuntu', 'debian',
                                   'mageia', 'fedora', 'opensuse', 'centos',
                                   'slackware', 'red hat', 'rhl', 'arch',
                                   'chaletos', 'crunchbang', 'elive', 'knoppix', 'mepis',
                                   'gentoo', 'mandriva',)):
        return 'GNU/Linux'
    else:
        return 'Other'


def get_browser_gp_group_by_family(family: str):
    family = family.lower()
    if 'Chrome Mobile'.lower() in family:
        return 'Chrome Mobile'
    elif 'Edge'.lower() in family:
        return 'Edge'
    elif 'Mobile Safari'.lower() in family:
        return 'Safari Mobile'
    elif 'MSIE'.lower() in family:
        return 'MSIE'
    elif 'Opera'.lower() in family:
        return 'Opera'
    elif 'Safari'.lower() in family:
        return 'Safari'
    elif 'Samsung Internet'.lower() in family:
        return 'Samsung Internet'
    elif any(w in family for w in ('YandexSearch'.lower(), 'Яндекс.Браузер'.lower())):
        return 'Яндекс.Браузер'
    elif any(w in family for w in ('Chromium'.lower(), 'Google Chrome'.lower(), 'GoogleSearch'.lower())):
        return 'Google Chrome'
    elif any(w in family for w in ('Firefox'.lower(), 'Firefox Mobile'.lower())):
        return 'Firefox'
    else:
        return 'Other'
