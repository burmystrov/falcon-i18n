import gettext as gettext_module
import os
import re
from collections import OrderedDict
from functools import lru_cache
from threading import local

import config

from . import func

# Keeps cache of translations so that not to load it again.
_trans = {}

# _active is used as thread-safe local object for keeping the language
_active = local()

_default = None

# Format of Accept-Language header values. From RFC 2616, section 14.4 and 3.9
# and RFC 3066, section 2.1
accept_language_re = re.compile(
    r'''
([a-z]{1,8}(?:-[a-z0-9]{1,8})*|\*)      # "en", "en-au", "x-y-z", "es-419", "*"
(?:\s*;\s*q=(0(?:\.\d{,3})?|1(?:\.0{,3})?))?  # Optional "q=1.00", "q=0.8"
(?:\s*,\s*|$)                                 # Multiple accepts per header.
    ''', re.VERBOSE)

language_code_re = re.compile(r'^[a-z]{1,8}(?:-[a-z0-9]{1,8})*$')


def to_locale(language, to_lower=False):
    """
    Turn a language name (en-us) into a locale name (en_US). If 'to_lower' is
    True, the last component is lower-cased (en_us).
    """
    p = language.find('-')
    if p >= 0:
        if to_lower:
            return language[:p].lower() + '_' + language[p + 1:].lower()
        else:
            # Get correct locale for sr-latn
            if len(language[p + 1:]) > 2:
                return (language[:p].lower() + '_' + language[p + 1].upper() +
                        language[p + 2:].lower())
            return language[:p].lower() + '_' + language[p + 1:].upper()
    else:
        return language.lower()


def get_languages():
    return OrderedDict(config.LANGUAGES)


def activate(language_code):
    if language_code:
        _active.value = translation(language_code)


def translation(language_code):
    if language_code not in _trans:
        _trans[language_code] = Translation(language_code)

    return _trans[language_code]


def gettext_noop(message):
    return message


def gettext(message):
    global _default

    message = message.replace('\r\n', '\n').replace('\r', '\n')

    if not len(message):
        return ''

    _default = _default or translation(config.LANGUAGE_CODE)
    tran = getattr(_active, 'value', _default)
    return tran.gettext(message)


lazy_gettext = func.lazy(gettext, str)


def get_language():
    """Returns currently chosen language.
    In case if the language isn't set It will return default language code
    """
    val = getattr(_active, 'value', None)
    return val.language if val else config.LANGUAGE_CODE


@lru_cache(maxsize=512)
def get_supported_lang_variant(lang_code):
    if lang_code:
        possible_variants = [lang_code, ]
        generic_variant = lang_code.split('-')[0]

        if lang_code != generic_variant:
            possible_variants.append(generic_variant)

        supported_languages = get_languages()

        for code in possible_variants:
            if code in supported_languages:
                return code

        # Attempt to use generic variant
        for code in supported_languages:
            if code.startswith(generic_variant + '-'):
                return code

    raise LookupError(lang_code)


def get_language_from_request(request):
    accept = request.get_header('accept-language')

    if accept:
        for lang_code, _ in parse_accept_lang_header(accept):
            # Asterisk means to use default language code
            if lang_code == '*':
                break

            if language_code_re.search(lang_code):
                try:
                    return get_supported_lang_variant(lang_code)
                except LookupError:
                    continue

    # The default language code is used as fallback
    try:
        return get_supported_lang_variant(config.LANGUAGE_CODE)
    except LookupError:
        return config.LANGUAGE_CODE


def parse_accept_lang_header(lang_string):
    """Parse the lang_string, which is the body of an Accept-Language
    header, and return a list of (lang, q-value), ordered by 'q' values.
    Return an empty list if there are any format errors in lang_string.
    """
    pieces = accept_language_re.split(lang_string.lower())
    if pieces[-1]:
        return []

    result = []
    for i in range(0, len(pieces) - 1, 3):
        first, lang, priority = pieces[i:i + 3]
        if first:
            return []
        result.append((lang, float(priority) if priority else 1.0))
    result.sort(key=lambda k: k[1], reverse=True)

    return result


class Translation(gettext_module.GNUTranslations):
    domain = 'mgo'

    def __init__(self, language):
        super().__init__()

        self.language = language
        self._to_locale = to_locale(language)
        self._catalog = None
        self.plural = lambda n: int(n != 1)  # germanic plural by default

        self._init_trans_catalog()

    def _new_gnu_trans(self, locale_dir, use_null_fallback=True):
        """Initiates mergeable `getttext.GNUTranslations` instance."""
        return gettext_module.translation(
            domain=self.domain,
            localedir=locale_dir,
            languages=[self._to_locale],
            codeset='utf-8',
            fallback=use_null_fallback
        )

    def _init_trans_catalog(self):
        locale_dir = os.path.join(os.path.dirname(config.__file__), 'locale')
        self.merge(self._new_gnu_trans(locale_dir))

        if self._catalog is None:
            self._catalog = {}

    def merge(self, other):
        """Merge another translation into this catalog."""
        if not getattr(other, '_catalog', None):
            return  # NullTranslations() has no _catalog

        if self._catalog is None:
            # Take plural and info from first catalog
            self.plural = other.plural
            self._info = other._info.copy()
            self._catalog = other._catalog.copy()
        else:
            self._catalog.update(other._catalog)
