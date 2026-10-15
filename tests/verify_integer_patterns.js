// Read generated datatype schemas on stdin. Uses only Node.js built-ins.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const schemas = JSON.parse(fs.readFileSync(0, 'utf8'));
const bounds = {
    int: [-2147483648n, 2147483647n],
    long: [-9223372036854775808n, 9223372036854775807n],
};
let checks = 0;

for (const [datatype, schema] of Object.entries(schemas)) {
    const pattern = new RegExp(schema.pattern);
    for (const invalid of ['', '+', '-', '1.5', '1e3', '42\n', '42\u2028', '--1', '+-1']) {
        assert(!pattern.test(invalid), `${datatype}: ${JSON.stringify(invalid)}`);
        checks++;
    }
    if (bounds[datatype]) {
        const [lo, hi] = bounds[datatype];
        const values = [lo - 1n, lo, lo + 1n, -1n, 0n, 1n, hi - 1n, hi, hi + 1n];
        let state = 2026n;
        for (let i = 0; i < 300; i++) {
            state = (state * 6364136223846793005n + 1442695040888963407n) % (1n << 65n);
            values.push(state - (1n << 64n));
        }
        for (const value of values) {
            const magnitude = value < 0n ? -value : value;
            const padded = (value < 0n ? '-' : '+') + '000' + magnitude.toString();
            for (const lexical of [value.toString(), padded]) {
                assert.equal(pattern.test(lexical), value >= lo && value <= hi, lexical);
                checks++;
            }
        }
    } else {
        for (const lexical of ['9007199254740992', '-9007199254740993',
            '1234567890123456789012345678901234567890', '+00042', '-00042', '-0']) {
            assert(pattern.test(lexical), lexical);
            checks++;
        }
    }
    for (const value of [schema.minimum - 1, schema.minimum, schema.maximum, schema.maximum + 1]) {
        const valid = Number.isInteger(value) && value >= schema.minimum && value <= schema.maximum;
        const expected = Number.isSafeInteger(value) && (!bounds[datatype] ||
            (BigInt(value) >= bounds[datatype][0] && BigInt(value) <= bounds[datatype][1]));
        assert.equal(valid, expected);
        checks++;
    }
}

// Evaluate the actual JavaScript template used to send Python code to Pyodide.
const html = fs.readFileSync(path.join(__dirname, '../playground/index.html'), 'utf8');
const embedded = html.match(/runPythonAsync\((String\.raw`([\s\S]*?)`)\);/);
assert(embedded, 'Playground converter must use a raw template');
assert.equal(vm.runInNewContext(embedded[1]), embedded[2]);
checks++;

const exact = '9007199254740993';
assert.equal(JSON.parse(JSON.stringify({ count: exact })).count, exact);
assert(JSON.parse('{"count":9007199254740993}').count > schemas.integer.maximum);
console.log(`${checks} assertions passed: ECMAScript patterns, BigInt ranges, safe numeric bounds, and playground Python escaping.`);
