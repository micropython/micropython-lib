import pprint
from io import StringIO
import sys

# setup


def pformat_as_pprint(*args, stream=None, **kwargs):
    """Use pformat() to provide pprint() interface"""
    val = pprint.pformat(*args, **kwargs)
    if not stream:
        stream = sys.stdout
    stream.write(val)
    stream.write("\n")


def pp_as_pprint(*args, sort_dicts=True, **kwargs):
    """Use pp() to provide pprint() interface"""
    pprint.pp(*args, sort_dicts=sort_dicts, **kwargs)


def PrettyPrinter_pprint_as_pprint(obj, *args, **kwargs):
    """Use PrettyPrinter.pprint() to provide pprint() interface"""
    p = pprint.PrettyPrinter(*args, **kwargs)
    p.pprint(obj)


def PrettyPrinter_pformat_as_pprint(obj, *args, **kwargs):
    """Use PrettyPrinter.pformat() to provide pprint() interface"""
    p = pprint.PrettyPrinter(*args, **kwargs)
    val = p.pformat(obj)
    p._stream.write(val)
    p._stream.write("\n")


pprint_func_map = {
    "pprint": pprint.pprint,
    "pformat": pformat_as_pprint,
    "pp": pp_as_pprint,
    "PrettyPrinter.pprint": PrettyPrinter_pprint_as_pprint,
    "PrettyPrinter.pformat": PrettyPrinter_pformat_as_pprint,
}


def pprint_func_to_pformat_func(pprint_func):
    """Convert pprint() interface into the pformat() interface"""

    def pformat_func(*args, **kwargs):
        sio = StringIO()
        pprint_func(*args, stream=sio, **kwargs)
        return sio.getvalue()[:-1]  # return all but the trailing newline

    return pformat_func


pformat_func_map = {key: pprint_func_to_pformat_func(val) for key, val in pprint_func_map.items()}
# reset the pformat function instead of two indirect wrappers
pformat_func_map["pformat"] = pprint.pformat


# test functions


def test_stream(name, pprint_func):
    # TODO: somehow test that stream=None goes to stdout
    # This method of mocking stdout works in CPython, but not Micropython
    # try:
    #    # mock standard out
    #    oldstdout = sys.stdout
    #    sys.stdout = sio
    #    # run test
    #    #...
    # finally:
    #    # restore standard out
    #    sys.stdout = oldstdout

    sio = StringIO()
    sio2 = StringIO()
    gen_msg = lambda s: f"{name}: {repr(s.getvalue())}"
    pprint_func("abcdefg", stream=sio2)
    assert sio.getvalue() == "", gen_msg(sio)
    assert sio2.getvalue() == "'abcdefg'\n", gen_msg(sio2)
    pprint_func("zxcvbnm", stream=sio)
    assert sio.getvalue() == "'zxcvbnm'\n", gen_msg(sio)
    assert sio2.getvalue() == "'abcdefg'\n", gen_msg(sio2)


def test_non_containers(name, pformat_func):
    class A:
        def __repr__(self):
            return "\n\ncocoa\n\nnuts\n\n"

    assert pformat_func(1) == repr(1), f"{name}, {pformat_func(1)}"
    assert pformat_func(1.423) == repr(1.423), name
    assert pformat_func("hello") == repr("hello"), name
    assert pformat_func(b"my grail diary") == repr(b"my grail diary"), name
    assert pformat_func(A()) == repr(A()), name


def test_empty_containers(name, pformat_func):
    assert pformat_func(list()) == "[]", name
    assert pformat_func(tuple()) == "()", name
    assert pformat_func(set()) == "set()", name
    assert pformat_func(dict()) == "{}", name


def test_containers_with_one_item(name, pformat_func):
    assert pformat_func(["abc"]) == repr(["abc"]), name
    assert pformat_func({123}) == repr({123}), name
    assert pformat_func({"abc": 123}) == repr({"abc": 123}), name
    assert pformat_func(("my tuple",)) == repr(("my tuple",)), name


X = {
    "widget": {
        "debug": "on",
        "window": {
            "title": "Sample Konfabulator Widget",
            "name": "main_window",
            "width": 500,
            "height": 500,
        },
        "image": {
            "src": "Images/Sun.png",
            "name": "sun1",
            "hOffset": 250,
            "vOffset": 250,
            "alignment": "center",
        },
        "text": {
            "data": "Click Here",
            "size": 36,
            "style": "bold",
            "name": "text1",
            "hOffset": 250,
            "vOffset": 100,
            "alignment": "center",
            "onMouseUp": "sun1.opacity = (sun1.opacity / 100) * 90;",
        },
    },
    "name": "King Arthur",
}

expected_X_depth0_indent0 = repr(X)
expected_X_depth0_indent1 = expected_X_depth0_indent0
expected_X_depth0_indent2 = expected_X_depth0_indent0
expected_X_depth0_indent3 = expected_X_depth0_indent0

# note: these are sorted by key and will be tested that way
expected_X_depth1_indent0 = (
    "{'name': " + repr(X["name"]) + ",\n" + "'widget': " + repr(X["widget"]) + "}"
)
expected_X_depth1_indent1 = (
    "{'name': " + repr(X["name"]) + ",\n" + " 'widget': " + repr(X["widget"]) + "}"
)
expected_X_depth1_indent2 = (
    "{ 'name': " + repr(X["name"]) + ",\n" + "  'widget': " + repr(X["widget"]) + "}"
)
expected_X_depth1_indent3 = (
    "{  'name': " + repr(X["name"]) + ",\n" + "   'widget': " + repr(X["widget"]) + "}"
)

expected_X_depth2_indent0 = (
    "{'name': 'King Arthur',\n"
    "'widget': {'debug': "
    + repr(X["widget"]["debug"])
    + ",\n"
    + "          'image': "
    + repr(X["widget"]["image"])
    + ",\n"
    + "          'text': "
    + repr(X["widget"]["text"])
    + ",\n"
    + "          'window': "
    + repr(X["widget"]["window"])
    + "}}"
)
expected_X_depth2_indent1 = (
    "{'name': 'King Arthur',\n"
    " 'widget': {'debug': "
    + repr(X["widget"]["debug"])
    + ",\n"
    + "            'image': "
    + repr(X["widget"]["image"])
    + ",\n"
    + "            'text': "
    + repr(X["widget"]["text"])
    + ",\n"
    + "            'window': "
    + repr(X["widget"]["window"])
    + "}}"
)
expected_X_depth2_indent2 = (
    "{ 'name': 'King Arthur',\n"
    "  'widget': { 'debug': "
    + repr(X["widget"]["debug"])
    + ",\n"
    + "              'image': "
    + repr(X["widget"]["image"])
    + ",\n"
    + "              'text': "
    + repr(X["widget"]["text"])
    + ",\n"
    + "              'window': "
    + repr(X["widget"]["window"])
    + "}}"
)
expected_X_depth2_indent3 = (
    "{  'name': 'King Arthur',\n"
    "   'widget': {  'debug': "
    + repr(X["widget"]["debug"])
    + ",\n"
    + "                'image': "
    + repr(X["widget"]["image"])
    + ",\n"
    + "                'text': "
    + repr(X["widget"]["text"])
    + ",\n"
    + "                'window': "
    + repr(X["widget"]["window"])
    + "}}"
)

expected_X_depth3_indent0 = (
    "{'name': 'King Arthur',\n"
    "'widget': {'debug': 'on',\n"
    "          'image': {'alignment': "
    + repr(X["widget"]["image"]["alignment"])
    + ",\n"
    + "                   'hOffset': "
    + repr(X["widget"]["image"]["hOffset"])
    + ",\n"
    "                   'name': " + repr(X["widget"]["image"]["name"]) + ",\n"
    "                   'src': " + repr(X["widget"]["image"]["src"]) + ",\n"
    "                   'vOffset': " + repr(X["widget"]["image"]["vOffset"]) + "},\n"
    "          'text': {'alignment': "
    + repr(X["widget"]["text"]["alignment"])
    + ",\n"
    + "                  'data': "
    + repr(X["widget"]["text"]["data"])
    + ",\n"
    + "                  'hOffset': "
    + repr(X["widget"]["text"]["hOffset"])
    + ",\n"
    + "                  'name': "
    + repr(X["widget"]["text"]["name"])
    + ",\n"
    + "                  'onMouseUp': "
    + repr(X["widget"]["text"]["onMouseUp"])
    + ",\n"
    + "                  'size': "
    + repr(X["widget"]["text"]["size"])
    + ",\n"
    + "                  'style': "
    + repr(X["widget"]["text"]["style"])
    + ",\n"
    + "                  'vOffset': "
    + repr(X["widget"]["text"]["vOffset"])
    + "},\n"
    + "          'window': {'height': "
    + repr(X["widget"]["window"]["height"])
    + ",\n"
    + "                    'name': "
    + repr(X["widget"]["window"]["name"])
    + ",\n"
    + "                    'title': "
    + repr(X["widget"]["window"]["title"])
    + ",\n"
    + "                    'width': "
    + repr(X["widget"]["window"]["width"])
    + "}}}"
)
expected_X_depth3_indent1 = (
    "{'name': 'King Arthur',\n"
    " 'widget': {'debug': 'on',\n"
    "            'image': {'alignment': "
    + repr(X["widget"]["image"]["alignment"])
    + ",\n"
    + "                      'hOffset': "
    + repr(X["widget"]["image"]["hOffset"])
    + ",\n"
    "                      'name': " + repr(X["widget"]["image"]["name"]) + ",\n"
    "                      'src': " + repr(X["widget"]["image"]["src"]) + ",\n"
    "                      'vOffset': " + repr(X["widget"]["image"]["vOffset"]) + "},\n"
    "            'text': {'alignment': "
    + repr(X["widget"]["text"]["alignment"])
    + ",\n"
    + "                     'data': "
    + repr(X["widget"]["text"]["data"])
    + ",\n"
    + "                     'hOffset': "
    + repr(X["widget"]["text"]["hOffset"])
    + ",\n"
    + "                     'name': "
    + repr(X["widget"]["text"]["name"])
    + ",\n"
    + "                     'onMouseUp': "
    + repr(X["widget"]["text"]["onMouseUp"])
    + ",\n"
    + "                     'size': "
    + repr(X["widget"]["text"]["size"])
    + ",\n"
    + "                     'style': "
    + repr(X["widget"]["text"]["style"])
    + ",\n"
    + "                     'vOffset': "
    + repr(X["widget"]["text"]["vOffset"])
    + "},\n"
    + "            'window': {'height': "
    + repr(X["widget"]["window"]["height"])
    + ",\n"
    + "                       'name': "
    + repr(X["widget"]["window"]["name"])
    + ",\n"
    + "                       'title': "
    + repr(X["widget"]["window"]["title"])
    + ",\n"
    + "                       'width': "
    + repr(X["widget"]["window"]["width"])
    + "}}}"
)
expected_X_depth3_indent2 = (
    "{ 'name': 'King Arthur',\n"
    "  'widget': { 'debug': 'on',\n"
    "              'image': { 'alignment': "
    + repr(X["widget"]["image"]["alignment"])
    + ",\n"
    + "                         'hOffset': "
    + repr(X["widget"]["image"]["hOffset"])
    + ",\n"
    "                         'name': " + repr(X["widget"]["image"]["name"]) + ",\n"
    "                         'src': " + repr(X["widget"]["image"]["src"]) + ",\n"
    "                         'vOffset': " + repr(X["widget"]["image"]["vOffset"]) + "},\n"
    "              'text': { 'alignment': "
    + repr(X["widget"]["text"]["alignment"])
    + ",\n"
    + "                        'data': "
    + repr(X["widget"]["text"]["data"])
    + ",\n"
    + "                        'hOffset': "
    + repr(X["widget"]["text"]["hOffset"])
    + ",\n"
    + "                        'name': "
    + repr(X["widget"]["text"]["name"])
    + ",\n"
    + "                        'onMouseUp': "
    + repr(X["widget"]["text"]["onMouseUp"])
    + ",\n"
    + "                        'size': "
    + repr(X["widget"]["text"]["size"])
    + ",\n"
    + "                        'style': "
    + repr(X["widget"]["text"]["style"])
    + ",\n"
    + "                        'vOffset': "
    + repr(X["widget"]["text"]["vOffset"])
    + "},\n"
    + "              'window': { 'height': "
    + repr(X["widget"]["window"]["height"])
    + ",\n"
    + "                          'name': "
    + repr(X["widget"]["window"]["name"])
    + ",\n"
    + "                          'title': "
    + repr(X["widget"]["window"]["title"])
    + ",\n"
    + "                          'width': "
    + repr(X["widget"]["window"]["width"])
    + "}}}"
)
expected_X_depth3_indent3 = (
    "{  'name': 'King Arthur',\n"
    "   'widget': {  'debug': 'on',\n"
    "                'image': {  'alignment': "
    + repr(X["widget"]["image"]["alignment"])
    + ",\n"
    + "                            'hOffset': "
    + repr(X["widget"]["image"]["hOffset"])
    + ",\n"
    "                            'name': " + repr(X["widget"]["image"]["name"]) + ",\n"
    "                            'src': " + repr(X["widget"]["image"]["src"]) + ",\n"
    "                            'vOffset': " + repr(X["widget"]["image"]["vOffset"]) + "},\n"
    "                'text': {  'alignment': "
    + repr(X["widget"]["text"]["alignment"])
    + ",\n"
    + "                           'data': "
    + repr(X["widget"]["text"]["data"])
    + ",\n"
    + "                           'hOffset': "
    + repr(X["widget"]["text"]["hOffset"])
    + ",\n"
    + "                           'name': "
    + repr(X["widget"]["text"]["name"])
    + ",\n"
    + "                           'onMouseUp': "
    + repr(X["widget"]["text"]["onMouseUp"])
    + ",\n"
    + "                           'size': "
    + repr(X["widget"]["text"]["size"])
    + ",\n"
    + "                           'style': "
    + repr(X["widget"]["text"]["style"])
    + ",\n"
    + "                           'vOffset': "
    + repr(X["widget"]["text"]["vOffset"])
    + "},\n"
    + "                'window': {  'height': "
    + repr(X["widget"]["window"]["height"])
    + ",\n"
    + "                             'name': "
    + repr(X["widget"]["window"]["name"])
    + ",\n"
    + "                             'title': "
    + repr(X["widget"]["window"]["title"])
    + ",\n"
    + "                             'width': "
    + repr(X["widget"]["window"]["width"])
    + "}}}"
)

expected_X_depth4_indent0 = expected_X_depth3_indent0
expected_X_depth4_indent1 = expected_X_depth3_indent1
expected_X_depth4_indent2 = expected_X_depth3_indent2
expected_X_depth4_indent3 = expected_X_depth3_indent3

expected_X_depth_None_indent0 = expected_X_depth3_indent0
expected_X_depth_None_indent1 = expected_X_depth3_indent1
expected_X_depth_None_indent2 = expected_X_depth3_indent2
expected_X_depth_None_indent3 = expected_X_depth3_indent3


def test_depth_and_indent(name, pformat_func):
    gen_msg = lambda d, i: f"{name} depth={d} indent={i}:\n{pformat_func(X, depth=d, indent=i)}\n"

    assert pformat_func(X, depth=0, indent=0) == expected_X_depth0_indent0, gen_msg(0, 0)
    assert pformat_func(X, depth=0, indent=1) == expected_X_depth0_indent1, gen_msg(0, 1)
    assert pformat_func(X, depth=0, indent=2) == expected_X_depth0_indent2, gen_msg(0, 3)
    assert pformat_func(X, depth=0, indent=3) == expected_X_depth0_indent3, gen_msg(0, 3)

    assert pformat_func(X, depth=1, indent=0) == expected_X_depth1_indent0, gen_msg(1, 0)
    assert pformat_func(X, depth=1, indent=1) == expected_X_depth1_indent1, gen_msg(1, 1)
    assert pformat_func(X, depth=1, indent=2) == expected_X_depth1_indent2, gen_msg(1, 3)
    assert pformat_func(X, depth=1, indent=3) == expected_X_depth1_indent3, gen_msg(1, 3)

    assert pformat_func(X, depth=2, indent=0) == expected_X_depth2_indent0, gen_msg(2, 0)
    assert pformat_func(X, depth=2, indent=1) == expected_X_depth2_indent1, gen_msg(2, 1)
    assert pformat_func(X, depth=2, indent=2) == expected_X_depth2_indent2, gen_msg(2, 3)
    assert pformat_func(X, depth=2, indent=3) == expected_X_depth2_indent3, gen_msg(2, 3)

    assert pformat_func(X, depth=3, indent=0) == expected_X_depth3_indent0, gen_msg(3, 0)
    assert pformat_func(X, depth=3, indent=1) == expected_X_depth3_indent1, gen_msg(3, 1)
    assert pformat_func(X, depth=3, indent=2) == expected_X_depth3_indent2, gen_msg(3, 3)
    assert pformat_func(X, depth=3, indent=3) == expected_X_depth3_indent3, gen_msg(3, 3)

    assert pformat_func(X, depth=4, indent=0) == expected_X_depth4_indent0, gen_msg(4, 0)
    assert pformat_func(X, depth=4, indent=1) == expected_X_depth4_indent1, gen_msg(4, 1)
    assert pformat_func(X, depth=4, indent=2) == expected_X_depth4_indent2, gen_msg(4, 3)
    assert pformat_func(X, depth=4, indent=3) == expected_X_depth4_indent3, gen_msg(4, 3)

    assert pformat_func(X, depth=None, indent=0) == expected_X_depth_None_indent0, gen_msg(None, 0)
    assert pformat_func(X, depth=None, indent=1) == expected_X_depth_None_indent1, gen_msg(None, 1)
    assert pformat_func(X, depth=None, indent=2) == expected_X_depth_None_indent2, gen_msg(None, 3)
    assert pformat_func(X, depth=None, indent=3) == expected_X_depth_None_indent3, gen_msg(None, 3)


# TODO: it would be good to test with sort_dicts=False


# run tests

for name, func in pprint_func_map.items():
    test_stream(name, func)

for name, func in pformat_func_map.items():
    test_non_containers(name, func)
    test_empty_containers(name, func)
    test_depth_and_indent(name, func)

#
# def test_depth(pformat_func):
#
