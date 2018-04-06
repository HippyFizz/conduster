from django.utils import translation


class LocaleMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        language = request.META.get('HTTP_LOCALE', 'en-US')
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

