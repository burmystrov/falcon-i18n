from utils import translation


class LocaleMiddleware:
    """This middleware is intended to determine and set language code into the
    current thread context allowing API resources to be dynamically translated
    per-request into different languages based on HTTP `Accept-Language` header.
    """

    def process_request(self, req, resp):
        language = translation.get_language_from_request(req)
        translation.activate(language)
        req.context['language_code'] = language

    def process_response(self, req, resp, resource):
        # Make sure the value is only set if it weren't determined somewhere
        # else.
        if not resp.get_header('content-language'):
            resp.set_header('content-language', translation.get_language())
