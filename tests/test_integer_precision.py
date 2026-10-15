"""Integer datatype coercion must preserve lossless JSON-LD string values."""

import json
import random

import pytest
from jsonschema import Draft7Validator, Draft202012Validator
from pyld import jsonld

from jsonldframe2schema import frame_to_schema

XSD = "http://www.w3.org/2001/XMLSchema#"
SAFE_INTEGER_MAX = 9007199254740991
BOUNDED_DATATYPES = [
    ("int", -2147483648, 2147483647),
    ("long", -9223372036854775808, 9223372036854775807),
]


def integer_frame(datatype="integer", container=None, expanded_type=False):
    definition = {
        "@id": "http://example.org/count",
        "@type": XSD + datatype if expanded_type else "xsd:" + datatype,
    }
    if container:
        definition["@container"] = container
    return {"@context": {"xsd": XSD, "count": definition}, "count": {}}


@pytest.mark.parametrize("datatype", ["integer", "int", "long"])
@pytest.mark.parametrize("expanded_type", [False, True])
def test_integer_coercion_accepts_native_and_lexical_values(datatype, expanded_type):
    schema = frame_to_schema(
        integer_frame(datatype, expanded_type=expanded_type), graph_only=True
    )
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    # Safe native integers remain valid; typed strings need no conversion.
    for value in [0, 42, -42, "0", "-0", "+42", "0042", "-42"]:
        assert validator.is_valid({"count": value}), repr(value)

    for value in [
        "",
        "+",
        "-",
        "1.5",
        "1e3",
        "NaN",
        "abc",
        "12x",
        " 42",
        "42 ",
        "42\n",
        "42\r\n",
        "42\u2028",
        "\u0661\u0662",
        1.5,
        True,
        None,
        [],
        {},
    ]:
        assert not validator.is_valid({"count": value}), repr(value)


@pytest.mark.parametrize(
    "datatype,value",
    [
        ("integer", "9007199254740993"),  # 2**53 + 1
        ("integer", "9007199254740992"),  # First unsafe positive integer
        ("integer", "-9007199254740992"),
        ("integer", "-9007199254740993"),
        ("integer", "1234567890123456789012345678901234567890"),
        ("integer", "+0042"),
        ("integer", "-0042"),
        ("integer", "-0"),
        ("long", "9223372036854775807"),
        ("long", "-9223372036854775808"),
        ("long", "+0009223372036854775807"),
        ("long", "-0009223372036854775808"),
        ("int", "2147483647"),
        ("int", "-2147483648"),
        ("int", "+0002147483647"),
        ("int", "-0002147483648"),
    ],
)
def test_framed_integer_strings_round_trip_without_precision_loss(datatype, value):
    frame = integer_frame(datatype)
    source = {
        "@id": "http://example.org/item",
        "http://example.org/count": {"@value": value, "@type": XSD + datatype},
    }
    framed = jsonld.frame(source, frame, {"omitGraph": False})
    serialized = json.loads(json.dumps(framed))

    assert serialized["@graph"][0]["count"] == value
    validator = Draft202012Validator(frame_to_schema(frame))
    validator.validate(serialized)
    expanded = jsonld.expand(serialized)
    assert expanded[0]["http://example.org/count"] == [
        {"@value": value, "@type": XSD + datatype}
    ]

    # Preserve the lexical form through RDF too, including signs and zeros.
    rdf = jsonld.to_rdf(serialized, {"format": "application/n-quads"})
    assert f'"{value}"^^<{XSD}{datatype}>' in rdf
    from_rdf = jsonld.from_rdf(
        rdf, {"format": "application/n-quads", "useNativeTypes": False}
    )
    reframed = jsonld.frame(from_rdf, frame, {"omitGraph": False})
    assert reframed["@graph"][0]["count"] == value
    validator.validate(reframed)


@pytest.mark.parametrize("datatype", ["integer", "int", "long"])
@pytest.mark.parametrize("container", ["@set", "@index"])
def test_integer_container_values_accept_exact_strings(datatype, container):
    schema = frame_to_schema(integer_frame(datatype, container), graph_only=True)
    validator = Draft202012Validator(schema)
    value = "2147483647" if datatype == "int" else "9007199254740993"
    values = {"first": value, "second": 42} if container == "@index" else [value, 42]
    invalid = {"first": "1.5"} if container == "@index" else ["1.5"]

    validator.validate({"count": values})
    assert not validator.is_valid({"count": invalid})
    unsafe = 2147483648 if datatype == "int" else 9007199254740992
    invalid = {"first": unsafe} if container == "@index" else [unsafe]
    assert not validator.is_valid({"count": invalid})


@pytest.mark.parametrize("datatype", ["double", "float", "decimal"])
def test_other_numeric_datatypes_keep_existing_number_mapping(datatype):
    schema = frame_to_schema(integer_frame(datatype), graph_only=True)
    assert schema["properties"]["count"] == {"type": "number"}
    validator = Draft202012Validator(schema)
    validator.validate({"count": 1.5})
    assert not validator.is_valid({"count": "1.5"})


def test_framed_native_integer_remains_numeric():
    frame = integer_frame()
    framed = jsonld.frame(
        {"@context": frame["@context"], "count": 42},
        frame,
        {"omitGraph": False},
    )
    assert framed["@graph"][0]["count"] == 42
    Draft202012Validator(frame_to_schema(frame)).validate(framed)


def test_uncoerced_integer_default_keeps_existing_mapping():
    schema = frame_to_schema(
        {"@context": {"count": "http://example.org/count"}, "count": 42},
        graph_only=True,
    )
    assert schema["properties"]["count"] == {"type": "integer", "default": 42}


def test_native_numeric_alternative_rejects_unsafe_and_rounded_values():
    # Model a JSON consumer that parses integers as binary64 numbers.
    parsed = json.loads('{"count":9007199254740993}', parse_int=float)
    assert parsed["count"] == 9007199254740992
    validator = Draft202012Validator(frame_to_schema(integer_frame(), graph_only=True))

    # Even after this unsafe integer rounds, it remains outside the safe range.
    assert not validator.is_valid(parsed)
    assert not validator.is_valid({"count": 9007199254740993})
    validator.validate({"count": "9007199254740993"})


@pytest.mark.parametrize("validator_class", [Draft7Validator, Draft202012Validator])
@pytest.mark.parametrize(
    "datatype,minimum,maximum",
    [
        ("integer", -SAFE_INTEGER_MAX, SAFE_INTEGER_MAX),
        ("long", -SAFE_INTEGER_MAX, SAFE_INTEGER_MAX),
        ("int", -2147483648, 2147483647),
    ],
)
def test_numeric_boundaries(validator_class, datatype, minimum, maximum):
    version = (
        "http://json-schema.org/draft-07/schema#"
        if validator_class is Draft7Validator
        else "https://json-schema.org/draft/2020-12/schema"
    )
    schema = frame_to_schema(
        integer_frame(datatype), schema_version=version, graph_only=True
    )
    validator_class.check_schema(schema)
    validator = validator_class(schema)
    for value in [
        minimum - 1,
        minimum,
        minimum + 1,
        -1,
        0,
        1,
        maximum - 1,
        maximum,
        maximum + 1,
        9007199254740993,
        -9007199254740993,
    ]:
        assert validator.is_valid({"count": value}) == (minimum <= value <= maximum)


@pytest.mark.parametrize("validator_class", [Draft7Validator, Draft202012Validator])
@pytest.mark.parametrize("datatype,minimum,maximum", BOUNDED_DATATYPES)
def test_bounded_lexical_ranges_against_exact_integer_arithmetic(
    validator_class, datatype, minimum, maximum
):
    schema = frame_to_schema(
        integer_frame(datatype),
        schema_version=validator_class.META_SCHEMA["$id"],
        graph_only=True,
    )
    validator_class.check_schema(schema)
    validator = validator_class(schema)
    cases = [
        minimum - 1,
        minimum,
        minimum + 1,
        -1,
        0,
        1,
        maximum - 1,
        maximum,
        maximum + 1,
    ]
    for exponent in range(1, len(str(maximum)) + 2):
        for delta in [-1, 0, 1]:
            cases.extend([10**exponent + delta, -(10**exponent + delta)])
    generator = random.Random(2026)
    cases.extend(generator.randint(minimum * 2, maximum * 2) for _ in range(200))

    for value in cases:
        expected = minimum <= value <= maximum
        sign = "-" if value < 0 else "+"
        representations = [str(value), f"{sign}000{abs(value)}"]
        if value >= 0:
            representations.append(f"000{value}")
        for lexical in representations:
            assert validator.is_valid({"count": lexical}) == expected, lexical


@pytest.mark.parametrize("value", [-SAFE_INTEGER_MAX, SAFE_INTEGER_MAX])
def test_safe_numeric_endpoints_survive_framing(value):
    frame = integer_frame()
    framed = jsonld.frame(
        {"@context": frame["@context"], "count": value}, frame, {"omitGraph": False}
    )
    serialized = json.loads(json.dumps(framed))
    assert serialized["@graph"][0]["count"] == value
    Draft202012Validator(frame_to_schema(frame)).validate(serialized)
