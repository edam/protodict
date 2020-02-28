# protodict

Is a fork of protobuf-to-dict (created by [Ben Hodgson](http://benhodgson.com/)),
stewarded by [Eugene Van den Bulke](http://github.com/3kwa) as Ben does not appear
to dedicate much time to it anymore.

protodict is a small Python library for 2 ways conversion between dicts
and protocol buffers.

## Installation

Use `pip install protodict` or `python setup.py install`.

## Example

Given the `google.protobuf.message.Message` subclass `MyMessage`:

```python
>>> import protodict
>>> my_message = MyMessage()
>>> # pb_my_message is a protobuf string
>>> my_message.ParseFromString(pb_my_message)
>>> protodict.to_dict(my_message)
{'message': 'Hello'}
```

## Caveats

### Base64 encoded `bytes`

This library grew out of the desire to serialize a protobuf-encoded message to
[JSON](http://json.org/). As JSON has no built-in binary type (all strings in
JSON are Unicode strings), a field whose type is `FieldDescriptor.TYPE_BYTES`
should be converted to a base64-encoded string.

If you want to encode bytes is this way, both `to_dict()` and `to_protobuf()`
take an optional `base64_bytes` argument:

```python
>>> # my_message is a google.protobuf.message.Message instance
>>> my_dict = to_dict(my_message, base64_bytes = True)
>>> to_protobuf(my_dict, base64_bytes = True)
```

### `int` vs. `str` enums

By default, the integer representation is used for enum values. To use their
string labels instead, pass `use_enum_labels=True` into `to_dict`:

```python
>>> to_dict(my_message, use_enum_labels=True)
```

## Unit testing

Tests are under `src/tests/`.

```sh
$ python setup.py nosetests
```

To regenerate `src/tests/sample_pb2.py`:

```sh
$ protoc --python_out=src -Isrc src/tests/sample.proto
```

## Authors

protodict is written and maintained by
[Ben Hodgson](http://benhodgson.com/), with significant contributions from
[Nino Walker](https://github.com/ninowalker),
[Jonathan Klaassen](https://github.com/jaklaassen), and
[Tristram Gräbener](http://blog.tristramg.eu/).
[Eugene Van den Bulke](http://github.com/3kwa)'s small contribution started with
a corner case bug fix and an ignored [PR](https://github.com/benhodgson/protobuf-to-dict/pull/5)
which led to this fork.

## (Un)license

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute
this software, either in source code form or as a compiled binary, for any
purpose, commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
