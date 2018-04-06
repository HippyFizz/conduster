import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from ua_parser import user_agent_parser

from collector.models import SessionStorage, Pixel, Event, OS, OSFamily, DeviceType, DeviceBrand, \
    Device, BrowserFamily, BrowserVersion, ScreenResolution, City
from collector.models.dictionaries import Provider, OSGroup
from utils.datetime import fromtimestamp_ms
from utils.ua import get_os_group_by_family

User = get_user_model()


def test_form(request):
    pixel = Pixel.objects.filter(
        project__title='Тестовый проект',
        project__user__username='root@conduster.com'
    ).first()
    return render(request, 'collector/test_form.html', {'pixel': pixel})


@csrf_exempt
def conduster_js(request):
    host = request.get_host() or 'dev-api.conduster.com'
    content = get_template('collector/conduster.js').template.source
    content = content.replace('{{ apiHost }}', host)
    return HttpResponse(content)


@csrf_exempt
@atomic()
def collect_event(request):
    data = json.loads(request.body.decode('utf-8'))
    session_id = data.get('session')
    if not session_id:
        return JsonResponse({'error': 'session required'}, status=400)
    try:
        session = SessionStorage.objects.get(id=session_id)
    except SessionStorage.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)
    except ValidationError:
        return JsonResponse({'error': 'Bad sessionId'}, status=400)

    parent_event = Event.objects\
        .filter(session=session)\
        .order_by('-finished').first()

    started = fromtimestamp_ms(data.get('started'))
    finished = fromtimestamp_ms(data.get('finished'))

    Event.objects.create(
        session=session,
        event_type=data.get('eventType'),
        started=started,
        finished=finished,
        duration=data.get('duration'),
        field_type=data.get('fieldType'),
        field_tag=data.get('fieldTag'),
        field_number=data.get('fieldNumber'),
        field_parent=parent_event,
        field_parent_number=parent_event.field_number if parent_event else None,
        field_hidden=data.get('fieldHidden', False),
        field_checked=data.get('fieldChecked', False),
        field_readonly=data.get('fieldReadonly', False),
        field_name=data.get('fieldName'),
        field_id=data.get('fieldId'),
        field_alt=data.get('fieldAlt'),
        field_title=data.get('fieldTitle'),
        field_data=data.get('fieldData'),
        field_accesskey=data.get('fieldAccesskey'),
        field_class=data.get('fieldClass'),
        field_contenteditable=data.get('fieldContenteditable'),
        field_contextmenu=data.get('fieldContextmenu'),
        field_dir=data.get('fieldDir'),
        field_lang=data.get('fieldLang'),
        field_spellcheck=data.get('fieldSpellcheck'),
        field_style=data.get('fieldStyle'),
        field_tabindex=data.get('fieldTabindex'),
        field_required=data.get('fieldRequired'),
        field_pattern=data.get('fieldPattern'),
        field_list=data.get('fieldList'),
        correction_count=data.get('correctionCount'),
        keypress_count=data.get('keypressCount'),
        special_keypress_count=data.get('specialKeypressCount'),
        text_length=data.get('textLength'),
        from_clipboard=data.get('fromClipboard'),
        open_data=data.get('openData'),
        hash_data=data.get('hashData'),
    )

    if data.get('eventType') == 'form-submitted':
        session.submitted = finished
        session.save(force_update=True, update_fields=('submitted',))

    return JsonResponse({})


@csrf_exempt
@atomic()
def open_session(request):
    data = json.loads(request.body.decode('utf-8'))
    ua_parsed = user_agent_parser.Parse(data.get('userAgent'))
    ip_addr = request.META.get('REMOTE_ADDR')

    #parse GEO data
    city = City.get_or_create_by_ip(ip_addr)

    pixel_id = data.get('pixelId')

    if not pixel_id:
        return JsonResponse({'error': 'pixelId required'}, status=400)

    try:
        pixel = Pixel.objects.get(id=pixel_id)
    except Pixel.DoesNotExist:
        return JsonResponse({'error': 'Pixel not found'}, status=404)

    #OS stuff
    os_family = (ua_parsed.get('os').get('family') or "other").lower()
    os_version = (ua_parsed.get('os').get('major') or "other").lower()
    os_version = "{} {}".format(os_family, os_version)
    os_group = get_os_group_by_family(os_family)
    os_group = OSGroup.objects.get(name=os_group)
    os_family, created = OSFamily.objects.get_or_create(
        name=os_family, defaults={'group': os_group}
    )
    os_version, created = OS.objects.get_or_create(family=os_family, name=os_version)

    #Device stuff
    device_type = (ua_parsed.get('device').get('family') or "other").lower()
    device_brand = (ua_parsed.get('device').get('brand') or "other").lower()
    device_model = (ua_parsed.get('device').get('model') or "other").lower()

    if device_type == "phone":
        device_type = DeviceType.PHONE
    elif device_type == "tablet":
        device_type = DeviceType.TABLET
    else:
        device_type = DeviceType.DESKTOP

    device_type = DeviceType.objects.get(category=device_type)
    device_brand, created = DeviceBrand.objects.get_or_create(name=device_brand)
    device, created = Device.objects.get_or_create(device_type=device_type,
        model=device_model, brand=device_brand)

    #Browser stuff
    browser_family = (ua_parsed.get('user_agent').get('family') or "other").lower()
    browser_version = (ua_parsed.get('user_agent').get('major') or "other").lower()
    browser = "{0} {1}".format(browser_family, browser_version)

    browser_family, created = BrowserFamily.objects.get_or_create(name=browser_family)
    browser_version, created = BrowserVersion.objects.get_or_create(family=browser_family,
        version=browser)

    #Screen stuff
    screen_height=data.get('screenHeight', 0)
    screen_width=data.get('screenWidth', 0)
    screen, created = ScreenResolution.objects.get_or_create(width=screen_width,
        height=screen_height)

    #provider stuff
    provider = Provider.get_or_create_by_ip(ip_addr)

    session = SessionStorage.objects.create(
        pixel=pixel,
        ip_addr=ip_addr,
        provider=provider,
        domain=data.get('domain'),
        get_params=data.get('getParams'),
        os_version=os_version,
        device=device,
        browser=browser_version,
        screen=screen,
        user_agent_string=data.get('userAgent'),
        cookie_enabled=data.get('cookieEnabled'),
        current_language=data.get('currentLanguage'),
        languages=str(data.get('languages')),
        geo=city,
        java_enabled=data.get('javaEnabled'),
        online=data.get('online'),
        plugin_list=data.get('pluginList'),
        canvas_byte_array = data.get('canvas'),
        webgl_vendor = data.get('webglVendor'),
        orientation = data.get('orientation'),
        ad_block = data.get('adBlock', False),
        has_ss = data.get('hasSS', False),
        has_ls = data.get('hasLS', False),
        has_idb = data.get('hasIDB', False),
        has_odb = data.get('hasODB', False),
        timezone_offset=data.get('timezoneOffset'),
        screen_color_depth=data.get('screenColorDepth'),
        location=data.get('location'),
        referrer=data.get('referrer'),
        page_title=data.get('pageTitle'),
        form_has_hidden_fields=data.get('formHasHiddenFields', False),
        viewport_height=data.get('viewPortHeight'),
        viewport_width=data.get('viewPortWidth'),
        available_height=data.get('avaliableHeight'),
        available_width=data.get('avaliableWidth'),
        page_total=data.get('pageTotal'),
        form_total_fields=data.get('totalFields'),
        form_hidden_fields=data.get('hiddenFields'),
        form_disabled_fields=data.get('disabledFields'),
    )

    fonts = data.get('fonts')
    if fonts:
        session.save_fonts(fonts)

    return JsonResponse({'sessionId': session.id})
