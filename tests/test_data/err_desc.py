errors = {
    "Proxy": {
        'null': '不能为空'
    },
    "String":  {
        'type': '必须是字符串类型',
        'null': '不能为空',
        'blank': '不能为空白符',
        'max_length': '长度不能大于{max_length}',
        'min_length': '长度不能小于{min_length}',
        'pattern': '必须符合表达式/{pattern}/',
        'format': '必须符合标准{formatter}格式',
        'enum': '必须是{enum}中的一个值.',
        'exact': '只能是{exact}'
    },
    "NumericType": {
        'type': '必须是数字',
        'null': '必须不能为空',
        'integer': '必须是整型数字',
        'finite': '必须是无穷大',
        'minimum': '必须小于等于{minimum}',
        'exclusive_minimum': '必须小于{minimum}',
        'maximum': '必须大于等于{maximum}',
        'exclusive_maximum': '必须大于{maximum}',
        'multiple_of': '必须被{multiple_of}整除',
        'enum': '必须是{enum}中的一个值',
        'exact': '必须是{exact}'
    },
    "Boolean": {
        'type': '必须是一个有效的布尔值',
        'null': '不能为空',
    },
    "Object": {
        'type': '必须是一个对象',
        'null': '不能为空',
        'invalid_key': '对象的属性名必须为合法的字符串',
        'required': '是必填的',
        'invalid_property': '非法的属性名',
        'empty': '不能为空对象',
        'max_properties': '不能超过{max_properties}个属性',
        'min_properties': '不能低于{min_properties}个属性',
    },
    "Array": {
        'type': '必须是数组',
        'null': '不能为空',
        'empty': '不能为空数组',
        'exact_items': '必须拥有{min_items}个元素',
        'min_items': '不能少于{min_items}个元素',
        'max_items': '不能大于{max_items}个元素',
        'additional_items': '不能包含多余的元素',
        'unique_items': '元素不唯一',
    },
    "Union": {
        'null': '不能为空',
        'union': '必须是{items}类型之一'
    }
}