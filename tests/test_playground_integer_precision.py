"""Run the playground's actual embedded converter, including JS string escaping."""

import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest
from jsonschema import Draft202012Validator
from pyld import jsonld

from jsonldframe2schema import FrameToSchemaConverter, frame_to_schema

ROOT = Path(__file__).parent.parent
XSD = "http://www.w3.org/2001/XMLSchema#"
SAFE_MAX = 9007199254740991


@pytest.fixture(scope="module")
def playground_converter():
    path = ROOT / "playground" / "index.html"
    html = path.read_text()
    match = re.search(r"runPythonAsync\(String\.raw`([\s\S]*?)`\);", html)
    assert match, "Embedded Python must use String.raw to preserve regex backslashes"
    namespace = {}
    exec(compile(match.group(1), str(path), "exec"), namespace)
    return namespace["frame_to_schema"]


@pytest.fixture(params=["integer", "int", "long"])
def frame(request):
    return {
        "@context": {
            "xsd": XSD,
            "count": {
                "@id": "http://example.org/count",
                "@type": "xsd:" + request.param,
            },
        },
        "count": {},
    }


def test_playground_integer_schema_matches_library(playground_converter, frame):
    assert playground_converter(frame) == frame_to_schema(frame, graph_only=True)


def test_playground_rejects_unsafe_numeric_values(playground_converter, frame):
    datatype = frame["@context"]["count"]["@type"]
    minimum, maximum = (
        (-2147483648, 2147483647) if datatype == "xsd:int" else (-SAFE_MAX, SAFE_MAX)
    )
    validator = Draft202012Validator(playground_converter(frame))
    for value in [minimum - 1, minimum, 0, maximum, maximum + 1, 9007199254740993]:
        assert validator.is_valid({"count": value}) == (minimum <= value <= maximum)


def test_playground_lexical_boundaries(playground_converter, frame):
    datatype = frame["@context"]["count"]["@type"]
    validator = Draft202012Validator(playground_converter(frame))
    for value in ["0", "-0", "+0042", "-0042"]:
        validator.validate({"count": value})
    for value in ["42\n", "42\r\n", "1.5", "1e3", "+-1", ""]:
        assert not validator.is_valid({"count": value})
    if datatype == "xsd:integer":
        validator.validate({"count": "1234567890123456789012345678901234567890"})
    else:
        minimum, maximum = (
            (-2147483648, 2147483647)
            if datatype == "xsd:int"
            else (-9223372036854775808, 9223372036854775807)
        )
        for value in [minimum - 1, minimum, maximum, maximum + 1]:
            lexical = ("-" if value < 0 else "+") + "000" + str(abs(value))
            assert validator.is_valid({"count": lexical}) == (
                minimum <= value <= maximum
            )


def test_playground_accepts_exact_framed_strings(playground_converter, frame):
    datatype = frame["@context"]["count"]["@type"]
    value = {
        "xsd:integer": "9007199254740993",
        "xsd:int": "-2147483648",
        "xsd:long": "-9223372036854775808",
    }[datatype]
    framed = jsonld.frame(
        {"@context": frame["@context"], "count": value}, frame, {"omitGraph": True}
    )
    serialized = json.loads(json.dumps(framed))
    assert serialized["count"] == value
    Draft202012Validator(playground_converter(frame)).validate(serialized)


def test_ecmascript_integer_patterns():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for ECMAScript regex verification")
    schemas = {
        datatype: FrameToSchemaConverter.TYPE_MAPPINGS[XSD + datatype]
        for datatype in ["integer", "int", "long"]
    }
    result = subprocess.run(
        [node, str(ROOT / "tests" / "verify_integer_patterns.js")],
        input=json.dumps(schemas),
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "assertions passed" in result.stdout
