# Amount-token boundary matrix - iteration 4

Status: **frozen before implementation**. This document and
`tests/acceptance/test_statement_import_review.py` are the complete iteration-4
amount-validity contract. No failure-specific branch or later one-case addition
is part of this handoff.

## Positive whitelist

A non-blank Debit or Credit token is valid if and only if all of these hold:

1. Its entire raw token matches the ASCII grammar
   `\+?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?`.
   No trimming, grouping, currency text, underscore, Unicode digit, or embedded
   whitespace is allowed. A leading `+`, a leading decimal point, a trailing
   decimal point, and scientific notation are deliberately valid grammar.
2. Its mathematical value is finite and non-negative. Every `-` spelling is
   invalid, including every negative-zero spelling.
3. Its value converts exactly to integer CAD cents, without context-dependent
   rounding, underflow, overflow, flags, or traps.
4. The non-negative cent magnitude is in the inclusive range
   `0..9223372036854775807`. The same magnitude boundary applies to Debit and
   Credit; Debit applies the negative sign only after validation.

For context-independent evaluation, combine the ASCII significand digits into
an integer coefficient and compute `scale = exponent - fractional_digits + 2`.
Zero coefficients map to zero cents regardless of exponent magnitude. For a
nonzero coefficient, a negative scale requires exact divisibility by the
corresponding power of ten; a non-negative scale appends zeros. Compare the
result with the SQLite maximum without Decimal-context arithmetic.

An empty or all-whitespace cell is **absent**, not a numeric token. If both
amount cells are absent the retained row remains `missing_amount`. Whitespace
around a nonblank number is not ignored. Two present cells remain
`ambiguous_amount` before numeric validation.

Every `V*` and `I*` case below runs through both Debit and Credit. Valid-table
minor units are unsigned magnitudes: Debit expects their negation and Credit
expects the listed value. Every invalid case expects one retained failed source
row, `error_code=invalid_amount`, zero occurrences, no normalized transaction,
and `parse_failed:invalid_amount`.

Notation used only to keep the table readable:

- `<Z1000>` = exactly 1,000 ASCII zero characters.
- `<E80>` = exactly 80 ASCII `9` characters.
- `\t`, `\x00`, `\u00a0`, `\u200b`, and `\ufeff` denote the literal tab,
  NUL, no-break space, zero-width space, and BOM characters used by the test.

## Valid guardrails

| ID | Raw token | Expected cents |
| --- | --- | ---: |
| V01 | `0` | 0 |
| V02 | `00.00` | 0 |
| V03 | `+0` | 0 |
| V04 | `.00` | 0 |
| V05 | `0.` | 0 |
| V06 | `0.01` | 1 |
| V07 | `.01` | 1 |
| V08 | `+.01` | 1 |
| V09 | `1` | 100 |
| V10 | `1.` | 100 |
| V11 | `001.23` | 123 |
| V12 | `1.2300` | 123 |
| V13 | `999.99` | 99999 |
| V14 | `92233720368547758.07` | 9223372036854775807 |
| V15 | `00092233720368547758.0700` | 9223372036854775807 |
| V16 | `1e0` | 100 |
| V17 | `1E+2` | 10000 |
| V18 | `+1e-2` | 1 |
| V19 | `123e-2` | 123 |
| V20 | `12300e-4` | 123 |
| V21 | `.1e1` | 100 |
| V22 | `.1e-1` | 1 |
| V23 | `1.e2` | 10000 |
| V24 | `001e-2` | 1 |
| V25 | `9223372036854775807e-2` | 9223372036854775807 |
| V26 | `9.223372036854775807e16` | 9223372036854775807 |
| V27 | `0e999999` | 0 |
| V28 | `0e-999999999` | 0 |
| V29 | `0e+<E80>` | 0 |
| V30 | `0e-<E80>` | 0 |
| V31 | `<Z1000>1.23` | 123 |
| V32 | `1.23<Z1000>` | 123 |
| V33 | `92233720368547758.07<Z1000>` | 9223372036854775807 |
| V34 | `1<Z1000>e-1000` | 100 |
| V35 | `1<Z1000>e-1002` | 1 |
| V36 | `123<Z1000>e-1002` | 123 |

These guardrails prevent an implementation from solving the red cases by
rejecting scientific notation, plus signs, noncanonical-but-valid decimal
points, long exact coefficients, long trailing zeros, or exact zero with an
extreme exponent.

## Invalid exceptional, sign, exactness, and range cases

| ID | Raw token | Expected outcome |
| --- | --- | --- |
| I01 | `NaN` | `invalid_amount` |
| I02 | `+NaN` | `invalid_amount` |
| I03 | `-NaN` | `invalid_amount` |
| I04 | `nan` | `invalid_amount` |
| I05 | `NaN123` | `invalid_amount` |
| I06 | `sNaN` | `invalid_amount` |
| I07 | `+sNaN` | `invalid_amount` |
| I08 | `-sNaN42` | `invalid_amount` |
| I09 | `Infinity` | `invalid_amount` |
| I10 | `+Infinity` | `invalid_amount` |
| I11 | `-Infinity` | `invalid_amount` |
| I12 | `Inf` | `invalid_amount` |
| I13 | `+inf` | `invalid_amount` |
| I14 | `-INF` | `invalid_amount` |
| I15 | `-0` | `invalid_amount` |
| I16 | `-0.00` | `invalid_amount` |
| I17 | `-.00` | `invalid_amount` |
| I18 | `-0e0` | `invalid_amount` |
| I19 | `-0E+999999` | `invalid_amount` |
| I20 | `-1` | `invalid_amount` |
| I21 | `-0.01` | `invalid_amount` |
| I22 | `-1e2` | `invalid_amount` |
| I23 | `0.001` | `invalid_amount` |
| I24 | `1.234` | `invalid_amount` |
| I25 | `0.009999999999999999` | `invalid_amount` |
| I26 | `92233720368547758.0701` | `invalid_amount` |
| I27 | `1.23<Z1000>1` | `invalid_amount` |
| I28 | `1e-3` | `invalid_amount` |
| I29 | `123e-3` | `invalid_amount` |
| I30 | `1.234e0` | `invalid_amount` |
| I31 | `1e-999999` | `invalid_amount` |
| I32 | `1e-999999999` | `invalid_amount` |
| I33 | `9.99e-1000000` | `invalid_amount` |
| I34 | `1e-<E80>` | `invalid_amount` |
| I35 | `92233720368547758.08` | `invalid_amount` |
| I36 | `92233720368547759` | `invalid_amount` |
| I37 | `9223372036854775808e-2` | `invalid_amount` |
| I38 | `9.223372036854775808e16` | `invalid_amount` |
| I39 | `1e17` | `invalid_amount` |
| I40 | `1e999999` | `invalid_amount` |
| I41 | `1e<E80>` | `invalid_amount` |
| I42 | `1<Z1000>` | `invalid_amount` |
| I43 | `123<Z1000>1e-1003` | `invalid_amount` |

## Invalid grammar, contamination, whitespace, and Unicode cases

| ID | Raw token | Expected outcome |
| --- | --- | --- |
| I44 | `1,234.56` | `invalid_amount` |
| I45 | `1.234,56` | `invalid_amount` |
| I46 | `1,23` | `invalid_amount` |
| I47 | `$1.00` | `invalid_amount` |
| I48 | `C$1.00` | `invalid_amount` |
| I49 | `CAD 1.00` | `invalid_amount` |
| I50 | `1.00 CAD` | `invalid_amount` |
| I51 | `1_000.00` | `invalid_amount` |
| I52 | `1 000.00` | `invalid_amount` |
| I53 | `1\u00a0000.00` | `invalid_amount` |
| I54 | `1'000.00` | `invalid_amount` |
| I55 | `(1.00)` | `invalid_amount` |
| I56 | `1.00-` | `invalid_amount` |
| I57 | `0x10` | `invalid_amount` |
| I58 | `0b10` | `invalid_amount` |
| I59 | `1/2` | `invalid_amount` |
| I60 | `100%` | `invalid_amount` |
| I61 | ` 1.00` | `invalid_amount` |
| I62 | `1.00 ` | `invalid_amount` |
| I63 | `\t1.00` | `invalid_amount` |
| I64 | `1.00\t` | `invalid_amount` |
| I65 | `1 .00` | `invalid_amount` |
| I66 | `1\t.00` | `invalid_amount` |
| I67 | `1e 2` | `invalid_amount` |
| I68 | `+ 1.00` | `invalid_amount` |
| I69 | `\u00a01.00` | `invalid_amount` |
| I70 | `\u200b1.00` | `invalid_amount` |
| I71 | `\ufeff1.00` | `invalid_amount` |
| I72 | `1.00\x00` | `invalid_amount` |
| I73 | `١.٢٣` | `invalid_amount` |
| I74 | `۱.۲۳` | `invalid_amount` |
| I75 | `१.२३` | `invalid_amount` |
| I76 | `１.２３` | `invalid_amount` |
| I77 | `１．２３` | `invalid_amount` |
| I78 | `−1.00` | `invalid_amount` |
| I79 | `＋1.00` | `invalid_amount` |
| I80 | `𝟙.𝟚𝟛` | `invalid_amount` |
| I81 | `١٫٢٣` | `invalid_amount` |
| I82 | `.` | `invalid_amount` |
| I83 | `+` | `invalid_amount` |
| I84 | `-` | `invalid_amount` |
| I85 | `1..0` | `invalid_amount` |
| I86 | `1.2.3` | `invalid_amount` |
| I87 | `1e` | `invalid_amount` |
| I88 | `1e+` | `invalid_amount` |
| I89 | `1e-` | `invalid_amount` |
| I90 | `e2` | `invalid_amount` |
| I91 | `.e2` | `invalid_amount` |
| I92 | `1ee2` | `invalid_amount` |
| I93 | `1e2.0` | `invalid_amount` |
| I94 | `1e++2` | `invalid_amount` |
| I95 | `1e--2` | `invalid_amount` |
| I96 | `++1` | `invalid_amount` |
| I97 | `+-1` | `invalid_amount` |
| I98 | `--1` | `invalid_amount` |
| I99 | `1E+ 2` | `invalid_amount` |
| I100 | `1d2` | `invalid_amount` |

## Absence and two-column semantics

| ID | Debit | Credit | Expected outcome |
| --- | --- | --- | --- |
| A01 | empty | empty | `missing_amount` |
| A02 | three spaces | empty | `missing_amount` |
| A03 | tab | empty | `missing_amount` |
| A04 | no-break space | empty | `missing_amount` |
| A05 | empty | three spaces | `missing_amount` |
| A06 | empty | tab | `missing_amount` |
| A07 | empty | no-break space | `missing_amount` |
| A08 | three spaces | `1.23` | valid Credit, `+123` |
| A09 | `1.23` | tab | valid Debit, `-123` |
| A10 | `1.00` | `2.00` | `ambiguous_amount` |

## Frozen verification contract

Exact command:

```text
python -m unittest tests.acceptance.test_statement_import_review -v
```

The matrix test is data-driven from the `VALID_AMOUNT_CASES`,
`INVALID_AMOUNT_CASES`, `MISSING_AMOUNT_CASES`, and
`ABSENT_COUNTERPART_CASES` constants. It checks all 36 valid tokens and all 100
invalid tokens through both Debit and Credit, plus the ten absence/ambiguity
cases: 282 matrix paths total. The fixture-field and failed-import recovery
acceptance tests remain in the same command.

## e94a09a baseline

The one frozen-matrix execution completed with exit 1: 3 test methods ran,
fixture-field and failed-import recovery tests remained green, and the matrix
reported 42 failing Debit/Credit subtests across 21 case IDs.

- **Red valid guardrails (over-rejected):** V29 and V30. Runtime-scale positive
  and negative exponents on a zero coefficient are mathematically zero but are
  rejected by the Decimal constructor/runtime boundary.
- **Red invalid cases (wrongly accepted):** I15-I19 (negative zero), I27 and
  I43 (long fractional tails rounded away), I32 (underflow to zero), I51
  (underscore grammar), I61-I64 and I69 (trimmed surrounding spaces/tabs/NBSP),
  and I73-I76 plus I80 (non-ASCII decimal digits).
- **Green valid guardrails:** V01-V28 and V31-V36.
- **Green invalid cases:** I01-I14, I20-I26, I28-I31, I33-I42, I44-I50,
  I52-I60, I65-I68, I70-I72, I77-I79, and I81-I100.
- **Green absence/two-column semantics:** A01-A10.

That is 42 red paths and 240 green paths out of the frozen 282-path matrix.
The exact command ran in 8.380 seconds and ended with
`FAILED (failures=42)`. No case was added or changed after this observation.
