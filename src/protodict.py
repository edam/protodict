import six
from google.protobuf.message import Message
from google.protobuf.descriptor import FieldDescriptor
from copy import copy


__all__ = [
    "to_dict",
    "TYPE_CALLABLE_MAP",
    "to_protobuf",
    "REVERSE_TYPE_CALLABLE_MAP"
]


EXTENSION_CONTAINER = '___X'

if six.PY2:
    _long = long
    _bytes = str
else:
    import base64
    _long = int
    _bytes = bytes


TYPE_CALLABLE_MAP = {
    FieldDescriptor.TYPE_DOUBLE: float,
    FieldDescriptor.TYPE_FLOAT: float,
    FieldDescriptor.TYPE_INT32: int,
    FieldDescriptor.TYPE_INT64: _long,
    FieldDescriptor.TYPE_UINT32: int,
    FieldDescriptor.TYPE_UINT64: _long,
    FieldDescriptor.TYPE_SINT32: int,
    FieldDescriptor.TYPE_SINT64: _long,
    FieldDescriptor.TYPE_FIXED32: int,
    FieldDescriptor.TYPE_FIXED64: _long,
    FieldDescriptor.TYPE_SFIXED32: int,
    FieldDescriptor.TYPE_SFIXED64: _long,
    FieldDescriptor.TYPE_BOOL: bool,
    FieldDescriptor.TYPE_STRING: six.text_type,
    FieldDescriptor.TYPE_BYTES: _bytes,
    FieldDescriptor.TYPE_ENUM: int,
}


def _repeated(type_callable):
    return lambda value_list: [type_callable(value) for value in value_list]


def _enum_label_name(field, value):
    return field.enum_type.values_by_number[int(value)].name


def _dec_bytes(value):
    return value.decode('base64') if six.PY2 else base64.b64decode(value)


def _enc_bytes(value):
    return value.encode("base64") if six.PY2 else base64.b64encode(value)


def to_dict(pb, type_callable_map=TYPE_CALLABLE_MAP, use_enum_labels=False, base64_bytes = False):
    result_dict = {}
    extensions = {}
    if base64_bytes:
        type_callable_map = copy(type_callable_map)
        type_callable_map[FieldDescriptor.TYPE_BYTES] = _enc_bytes
    for field, value in pb.ListFields():
        type_callable = _get_field_value_adaptor(pb, field, type_callable_map, use_enum_labels)
        if field.label == FieldDescriptor.LABEL_REPEATED:
            type_callable = _repeated(type_callable)

        if field.is_extension:
            extensions[str(field.number)] = type_callable(value)
            continue

        result_dict[field.name] = type_callable(value)

    if extensions:
        result_dict[EXTENSION_CONTAINER] = extensions
    return result_dict


def _get_field_value_adaptor(pb, field, type_callable_map=TYPE_CALLABLE_MAP, use_enum_labels=False):
    if field.type in (FieldDescriptor.TYPE_MESSAGE, FieldDescriptor.TYPE_GROUP):
        # recursively encode protobuf sub-message
        return lambda pb: to_dict(pb,
            type_callable_map=type_callable_map,
            use_enum_labels=use_enum_labels)

    if use_enum_labels and field.type == FieldDescriptor.TYPE_ENUM:
        return lambda value: _enum_label_name(field, value)

    if field.type in type_callable_map:
        return type_callable_map[field.type]

    raise TypeError("Field %s.%s has unrecognised type id %d" % (
        pb.__class__.__name__, field.name, field.type))


REVERSE_TYPE_CALLABLE_MAP = {}


def to_protobuf(pb_klass_or_instance, values, type_callable_map=REVERSE_TYPE_CALLABLE_MAP, strict=True, base64_bytes = False):
    """Populates a protobuf model from a dictionary.

    :param pb_klass_or_instance: a protobuf message class, or an protobuf instance
    :type pb_klass_or_instance: a type or instance of a subclass of google.protobuf.message.Message
    :param dict values: a dictionary of values. Repeated and nested values are
       fully supported.
    :param dict type_callable_map: a mapping of protobuf types to callables for setting
       values on the target instance.
    :param bool strict: complain if keys in the map are not fields on the message.
    """
    if isinstance(pb_klass_or_instance, Message):
        instance = pb_klass_or_instance
    else:
        instance = pb_klass_or_instance()
    if base64_bytes:
        type_callable_map = copy(type_callable_map)
        type_callable_map[FieldDescriptor.TYPE_BYTES] = _dec_bytes
    return _dict_to_protobuf(instance, values, type_callable_map, strict)


def _get_field_mapping(pb, dict_value, strict):
    field_mapping = []
    for key, value in dict_value.items():
        if key == EXTENSION_CONTAINER:
            continue
        if key not in pb.DESCRIPTOR.fields_by_name:
            if strict:
                raise KeyError("%s does not have a field called %s" % (pb, key))
            continue
        field_mapping.append((pb.DESCRIPTOR.fields_by_name[key], value, getattr(pb, key, None)))

    for ext_num, ext_val in dict_value.get(EXTENSION_CONTAINER, {}).items():
        try:
            ext_num = int(ext_num)
        except ValueError:
            raise ValueError("Extension keys must be integers.")
        if ext_num not in pb._extensions_by_number:
            if strict:
                raise KeyError("%s does not have a extension with number %s. Perhaps you forgot to import it?" % (pb, key))
            continue
        ext_field = pb._extensions_by_number[ext_num]
        pb_val = None
        pb_val = pb.Extensions[ext_field]
        field_mapping.append((ext_field, ext_val, pb_val))

    return field_mapping


def _dict_to_protobuf(pb, value, type_callable_map, strict):
    fields = _get_field_mapping(pb, value, strict)

    for field, input_value, pb_value in fields:
        if field.label == FieldDescriptor.LABEL_REPEATED:
            for item in input_value:
                if field.type in (FieldDescriptor.TYPE_MESSAGE, FieldDescriptor.TYPE_GROUP):
                    m = pb_value.add()
                    _dict_to_protobuf(m, item, type_callable_map, strict)
                elif field.type == FieldDescriptor.TYPE_ENUM and isinstance(item, six.string_types):
                    pb_value.append(_string_to_enum(field, item))
                else:
                    pb_value.append(item)
            continue
        if field.type in (FieldDescriptor.TYPE_MESSAGE, FieldDescriptor.TYPE_GROUP):
            if input_value:
                _dict_to_protobuf(pb_value, input_value, type_callable_map, strict)
            else:
                m = type(pb_value)()
                getattr(pb, field.name).MergeFrom(m)
            continue

        if field.type in type_callable_map:
            input_value = type_callable_map[field.type](input_value)

        if field.is_extension:
            pb.Extensions[field] = input_value
            continue

        if field.type == FieldDescriptor.TYPE_ENUM and isinstance(input_value, six.string_types):
            input_value = _string_to_enum(field, input_value)

        if input_value is None:
            pb.ClearField(field.name)
        else:
            setattr(pb, field.name, input_value)

    return pb

def _string_to_enum(field, input_value):
    enum_dict = field.enum_type.values_by_name
    try:
        input_value = enum_dict[input_value].number
    except KeyError:
        raise KeyError("`%s` is not a valid value for field `%s`" % (input_value, field.name))
    return input_value
