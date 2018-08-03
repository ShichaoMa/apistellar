import re
import uuid
import datetime

from apistar.exceptions import ValidationError

from ..helper import find_children


DATE_REGEX = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$'
)

TIME_REGEX = re.compile(
    r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
)

DATETIME_REGEX = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
    r'[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    r'(?P<tzinfo>Z|[+-]\d{2}(?::?\d{2})?)?$'
)


class BaseFormat(object):
    def __init__(self, **kwargs):
        pass

    def is_native_type(self, value):
        raise NotImplementedError()

    def validate(self, value):
        raise NotImplementedError()

    def to_string(self, value):
        raise NotImplementedError()


class DateFormat(BaseFormat):
    name = "date"
    type = datetime.date

    def is_native_type(self, value):
        return isinstance(value, self.type)

    def validate(self, value):
        match = DATE_REGEX.match(value)
        if not match:
            raise ValidationError('Must be a valid date.')

        kwargs = {k: int(v) for k, v in match.groupdict().items()}
        return datetime.date(**kwargs)

    def to_string(self, value):
        try:
            return value.isoformat()
        except AttributeError:
            if value:
                return str(value)


class TimeFormat(BaseFormat):
    name = "time"
    type = datetime.time

    def is_native_type(self, value):
        return isinstance(value, self.type)

    def validate(self, value):
        match = TIME_REGEX.match(value)
        if not match:
            raise ValidationError('Must be a valid time.')

        kwargs = match.groupdict()
        kwargs['microsecond'] = kwargs['microsecond'] and kwargs['microsecond'].ljust(6, '0')
        kwargs = {k: int(v) for k, v in kwargs.items() if v is not None}
        return datetime.time(**kwargs)

    def to_string(self, value):
        try:
            return value.isoformat()
        except AttributeError:
            if value is not None:
                return str(value)


class DateTimeFormat(BaseFormat):
    name = "datetime"
    type = datetime.datetime

    def is_native_type(self, value):
        return isinstance(value, self.type)

    def validate(self, value):
        match = DATETIME_REGEX.match(value)
        if not match:
            raise ValidationError('Must be a valid datetime.')

        kwargs = match.groupdict()
        kwargs['microsecond'] = kwargs['microsecond'] and kwargs['microsecond'].ljust(6, '0')
        tzinfo = kwargs.pop('tzinfo')
        if tzinfo == 'Z':
            tzinfo = datetime.timezone.utc
        elif tzinfo is not None:
            offset_mins = int(tzinfo[-2:]) if len(tzinfo) > 3 else 0
            offset_hours = int(tzinfo[1:3])
            delta = datetime.timedelta(hours=offset_hours, minutes=offset_mins)
            if tzinfo[0] == '-':
                delta = -delta
            tzinfo = datetime.timezone(delta)
        kwargs = {k: int(v) for k, v in kwargs.items() if v is not None}
        kwargs['tzinfo'] = tzinfo
        return datetime.datetime(**kwargs)

    def to_string(self, value):
        try:
            value = value.isoformat()
            if value.endswith('+00:00'):
                value = value[:-6] + 'Z'
            return value
        except AttributeError:
            if value is not None:
                return str(value)


class UUIDFormat(BaseFormat):
    name = "UUID"
    type = uuid.UUID

    def is_native_type(self, value):
        return isinstance(value, self.type)

    def validate(self, value):
        return value

    def to_string(self, value):
        if value is not None:
            return str(value)


class ChildrenFactory(object):

    def __init__(self, father, kwargs=None):
        self.father = father
        self.kwargs = kwargs or {}
        self.found = dict()

    def install(self, **kwargs):
        self.found.clear()
        self.kwargs.update(kwargs)

    def _get_mapping(self):
        return {getattr(child, "name", child.__name__.lower()): child
                for child in find_children(self.father, False)}

    def __contains__(self, item):
        result = item in self.found
        if result is False:
            result = item in self._get_mapping()
        return result

    def __getitem__(self, item):
        formatter = self.found.get(item)
        if formatter is None:
            mapping = self._get_mapping()
            assert item in mapping, "Format not found"
            formatter = mapping[item](**self.kwargs)
            self.found[item] = formatter
        return formatter

    def __setitem__(self, item, value):
        self.found[item] = value


FORMATS = ChildrenFactory(BaseFormat)


def install(**kwargs):
    FORMATS.install(**kwargs)