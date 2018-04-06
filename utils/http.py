from urllib.parse import _coerce_args, unquote

from django.utils.http import _urlparse


def urlparse_qs_or_fragment(url, param_names):
    """

    :param url:
    :param param_names: list of parameters to find
    :return: parset args from query or fragment? default form query
    >>> urlparse_qs_or_fragment(b'http://example.com?q1=1',[b'q1'])
    {b'q1': b'1'}
    >>> urlparse_qs_or_fragment(b'http://www.example.org/path?_openstat=openstat.ru;camp1;ad1234;top-left-corner', [b'_openstat'])
    {b'_openstat': b'openstat.ru;camp1;ad1234;top-left-corner'}
    >>> urlparse_qs_or_fragment(b'http://example.com#q1=f', [b'q1'])
    {b'q1': b'f'}
    >>> urlparse_qs_or_fragment(b'http://example.com?q1=q#q1=f', [b'q1'])
    {b'q1': b'q'}
    >>> urlparse_qs_or_fragment('http://example.com?q1=q', ['q1'])
    {'q1': 'q'}
    >>> urlparse_qs_or_fragment('http://example.com#q1=f', ['q1'])
    {'q1': 'f'}
    >>> urlparse_qs_or_fragment('http://example.com?q1=q#q1=f', ['q1'])
    {'q1': 'q'}
    """
    parsed = _urlparse(url)
    res = {}
    if parsed.query:
        res = find_params(parsed.query, param_names)
        if res:
            return res

    if parsed.fragment:
        res = find_params(parsed.fragment, param_names)
    return res


def find_params(querystring, param_names):
    """

    :param querystring:
    :param param_names:
    :return:
    """
    res = {}
    params = parse_qs(querystring)
    for name in param_names:
        if name in params:
            res[name] = params[name][0]
    return res


def parse_qs(qs, keep_blank_values=False, strict_parsing=False,
             encoding='utf-8', errors='replace'):
    """
    Copy of urlib.parse pars_qs but without splitting by semicolon
    Parse a query given as a string argument.

        Arguments:

        qs: percent-encoded query string to be parsed

        keep_blank_values: flag indicating whether blank values in
            percent-encoded queries should be treated as blank strings.
            A true value indicates that blanks should be retained as
            blank strings.  The default false value indicates that
            blank values are to be ignored and treated as if they were
            not included.

        strict_parsing: flag indicating what to do with parsing errors.
            If false (the default), errors are silently ignored.
            If true, errors raise a ValueError exception.

        encoding and errors: specify how to decode percent-encoded sequences
            into Unicode characters, as accepted by the bytes.decode() method.
    """
    parsed_result = {}
    pairs = parse_qsl(qs, keep_blank_values, strict_parsing,
                      encoding=encoding, errors=errors)
    for name, value in pairs:
        if name in parsed_result:
            parsed_result[name].append(value)
        else:
            parsed_result[name] = [value]
    return parsed_result


def parse_qsl(qs, keep_blank_values=False, strict_parsing=False,
              encoding='utf-8', errors='replace'):
    """
    Copy of urlib.parse pars_qsl but without splitting by semicolon
    Parse a query given as a string argument.

    Arguments:

    qs: percent-encoded query string to be parsed

    keep_blank_values: flag indicating whether blank values in
        percent-encoded queries should be treated as blank strings.  A
        true value indicates that blanks should be retained as blank
        strings.  The default false value indicates that blank values
        are to be ignored and treated as if they were  not included.

    strict_parsing: flag indicating what to do with parsing errors. If
        false (the default), errors are silently ignored. If true,
        errors raise a ValueError exception.

    encoding and errors: specify how to decode percent-encoded sequences
        into Unicode characters, as accepted by the bytes.decode() method.

    Returns a list, as G-d intended.
    >>> parse_qsl('_openstat=openstat.ru;camp1;ad1234;top-left-corner')
    [('_openstat', 'openstat.ru;camp1;ad1234;top-left-corner')]

    """
    qs, _coerce_result = _coerce_args(qs)
    pairs = [s1 for s1 in qs.split('&')]
    r = []
    for name_value in pairs:
        if not name_value and not strict_parsing:
            continue
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError("bad query field: %r" % (name_value,))
            # Handle case of a control-name with no equal sign
            if keep_blank_values:
                nv.append('')
            else:
                continue
        if len(nv[1]) or keep_blank_values:
            name = nv[0].replace('+', ' ')
            name = unquote(name, encoding=encoding, errors=errors)
            name = _coerce_result(name)
            value = nv[1].replace('+', ' ')
            value = unquote(value, encoding=encoding, errors=errors)
            value = _coerce_result(value)
            r.append((name, value))
    return r