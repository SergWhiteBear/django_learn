from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


def validate_global_group(value):
    regex_global_group = r'^МЕН-\d{6}$'
    if not re.match(regex_global_group, value):
        raise ValidationError(
            _("Введите группу в виде: МЕН-??????"),
            params={'value': value},
        )


def validate_local_group(value):
    regex_local_group = r'^[А-Я]{2}-\d{3}$'
    if not re.match(regex_local_group, value):
        raise ValidationError(
            _("Введите группу в виде: ??-???"),
            params={'value': value},
        )