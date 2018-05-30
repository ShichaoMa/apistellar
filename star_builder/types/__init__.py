import json

from abc import ABCMeta
from collections.abc import Mapping

from apistar.exceptions import ConfigurationError, ValidationError

from . import validators


class TypeMetaclass(ABCMeta):

    def __new__(mcs, name, bases, attrs):
        properties = []
        for key, value in list(attrs.items()):
            if key in ['keys', 'items', 'values', 'get', 'validator']:
                msg = (
                    'Cannot use reserved name "%s" on Type "%s", as it '
                    'clashes with the class interface.'
                )
                raise ConfigurationError(msg % (key, name))

            elif hasattr(value, 'validate'):
                attrs.pop(key)
                properties.append((key, value))

        # If this class is subclassing another Type, add that Type's properties.
        # Note that we loop over the bases in reverse. This is necessary in order
        # to maintain the correct order of properties.
        for base in reversed(bases):
            if hasattr(base, 'validator'):
                properties = [
                    (key, base.validator.properties[key]) for key
                    in base.validator.properties
                    if key not in attrs
                ] + properties

        properties = sorted(
            properties,
            key=lambda item: item[1]._creation_counter
        )
        required = [
            key for key, value in properties
            if not value.has_default()
        ]
        attrs['_creation_counter'] = validators.Validator._creation_counter
        validators.Validator._creation_counter += 1

        cls = super(TypeMetaclass, mcs).__new__(mcs, name, bases, attrs)

        cls.validator = validators.Object(
            def_name=name,
            properties=properties,
            required=required,
            additional_properties=None,
            model=cls,
            default=cls.has_default()
        )

        return cls


class Type(Mapping, metaclass=TypeMetaclass):

    driver = None

    def __init__(self, *args, **kwargs):
        definitions = None
        allow_coerce = False
        force_format = False

        if args:
            assert len(args) == 1
            definitions = kwargs.pop('definitions', definitions)
            allow_coerce = kwargs.pop('allow_coerce', allow_coerce)
            force_format = kwargs.pop('force_format', allow_coerce)
            assert not kwargs

            if args[0] is None or isinstance(args[0], (bool, int, float, list)):
                raise ValidationError('Must be an object.')
            elif isinstance(args[0], dict):
                # Instantiated with a dict.
                value = args[0]
            else:
                # Instantiated with an object instance.
                value = {
                    key: getattr(args[0], key)
                    for key in self.validator.properties.keys()
                }
        else:
            # Instantiated with keyword arguments.
            value = kwargs

        object.__setattr__(self, '_dict', value)
        object.__setattr__(self, 'formatted', False)
        if force_format:
            self.format()

    def format(self):
        if not self.formatted:
            object.__setattr__(self, '_dict', self.validator.validate(self._dict))
            object.__setattr__(self, 'formatted', True)

    @classmethod
    def validate(cls, value, definitions=None, allow_coerce=False, force_format=True):
        if cls.allow_null() and value is None:
            return value
        return cls(value,
                   definitions=definitions,
                   allow_coerce=allow_coerce,
                   force_format=force_format)

    @classmethod
    def allow_null(cls):
        return False

    @classmethod
    def has_default(cls):
        return False

    def __repr__(self):
        args = ['%s=%s' % (key, repr(value)) for key, value in self.items()]
        arg_string = ', '.join(args)
        return '<%s(%s)>' % (self.__class__.__name__, arg_string)

    def __setattr__(self, key, value):
        if key not in self.validator.properties:
            raise AttributeError('Invalid attribute "%s"' % key)
        value = self.validator.properties[key].validate(value)
        self._dict[key] = value

    def __setitem__(self, key, value):
        if key not in self.validator.properties:
            raise KeyError('Invalid key "%s"' % key)
        value = self.validator.properties[key].validate(value)
        self._dict[key] = value

    def __getattr__(self, key):
        try:
            return self._dict[key]
        except (KeyError,):
            raise AttributeError('Invalid attribute "%s"' % key)

    def __getitem__(self, key):
        self.format()
        value = self._dict[key]
        if value is None:
            return None
        validator = self.validator.properties[key]
        if hasattr(validator, 'format') and validator.format in validators.FORMATS:
            formatter = validators.FORMATS[validator.format]
            return formatter.to_string(value)
        return value

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        self.format()
        return iter(self._dict)

    @classmethod
    def init(cls, **kwargs):
        for k, v in kwargs.items():
            setattr(cls, k, v)

    def to_json(self, force_format=True):
        if force_format:
            return json.loads(json.dumps(self, cls=TypeEncoder))
        return self._dict


class TypeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Type):
            return dict(obj)
        return json.JSONEncoder.default(self, obj)
