import json

from abc import ABCMeta
from collections.abc import Mapping

from apistar.exceptions import ConfigurationError, ValidationError

from . import validators
from ..helper import TypeEncoder


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

        default = cls.has_default() or validators.NO_DEFAULT
        cls.validator = validators.Object(
            def_name=name,
            properties=properties,
            required=required,
            additional_properties=None,
            model=cls,
            default=default
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
            elif isinstance(args[0], Mapping):
                # Instantiated with a dict.
                value = args[0]
            else:
                # Instantiated with an object instance.
                value = {}
                for key, val in self.validator.properties.items():
                    v = getattr(args[0], key, None)
                    if not v and val.has_default():
                        v = val.get_default()
                    if v:
                        value[key] = v
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
        """
        或者直接返回default值
        :return:
        """
        return False

    @classmethod
    def get_default(cls):
        default = cls.has_default()
        assert default, (778, f"{cls} haven't got a value/default value!")
        if callable(default):
            return default()
        return default

    def __repr__(self):
        if self.formatted:
            pair = self.items()
        else:
            pair = self._dict.items()
        args = ['%s=%s' % (key, repr(value)) for key, value in pair]
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
            if key != "_dict":
                return self._dict[key]
            return object.__getattribute__(self, key)
        except (KeyError,):
            raise AttributeError('Invalid attribute "%s"' % key)

    def __getitem__(self, key):
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
        return iter(self._dict)

    @classmethod
    def init(cls, **kwargs):
        for k, v in kwargs.items():
            setattr(cls, k, v)

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_json(self):
        return json.loads(json.dumps(self, cls=TypeEncoder))