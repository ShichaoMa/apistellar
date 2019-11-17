errors = {
    "Validator": {},
    "Proxy": {
        'null': 'May not be null.'
    },
    "String":  {
        'type': 'Must be a string.',
        'null': 'May not be null.',
        'blank': 'Must not be blank.',
        'max_length': 'Must have no more than {max_length} characters',
        'min_length': 'Must have at least {min_length} characters',
        'pattern': 'Must match the pattern /{pattern}/.',
        'format': 'Must be a valid {format}.',
        'enum': 'Must be one of {enum}.',
        'exact': 'Must be {exact}.'
    },
    "NumericType": {
        'type': 'Must be a number.',
        'null': 'May not be null.',
        'integer': 'Must be an integer.',
        'finite': 'Must be finite.',
        'minimum': 'Must be greater than or equal to {minimum}.',
        'exclusive_minimum': 'Must be greater than {minimum}.',
        'maximum': 'Must be less than or equal to {maximum}.',
        'exclusive_maximum': 'Must be less than {maximum}.',
        'multiple_of': 'Must be a multiple of {multiple_of}.',
        'enum': 'Must be one of {enum}.',
        'exact': 'Must be {exact}.'
    },
    "Boolean": {
        'type': 'Must be a valid boolean.',
        'null': 'May not be null.',
    },
    "Object": {
        'type': 'Must be an object.',
        'null': 'May not be null.',
        'invalid_key': 'Object keys must be strings.',
        'required': 'The "{field_name}" field is required.',
        'invalid_property': 'Invalid property name.',
        'empty': 'Must not be empty.',
        'max_properties': 'Must have no more than {max_properties} properties.',
        'min_properties': 'Must have at least {min_properties} properties.',
    },
    "Array": {
        'type': 'Must be an array.',
        'null': 'May not be null.',
        'empty': 'Must not be empty.',
        'exact_items': 'Must have {min_items} items.',
        'min_items': 'Must have at least {min_items} items.',
        'max_items': 'Must have no more than {max_items} items.',
        'additional_items': 'May not contain additional items.',
        'unique_items': 'This item is not unique.',
    },
    "Union": {
        'null': 'Must not be null.',
        'union': 'Must match one of the union types.'
    }
}