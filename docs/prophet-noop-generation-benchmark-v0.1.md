# Prophet No-Op Generation Benchmark v0.1

Date: February 14, 2026

## Goal

Measure the no-op generation performance impact of `prophet gen --skip-unchanged` compared with regular `prophet gen` on unchanged ontology/config inputs.

## Method

1. Initialize a temporary Prophet project.
2. Copy `examples/java/prophet_example_spring/ontology/local/main.prophet`.
3. Run one warm-up `prophet gen`.
4. Run 12 iterations of:
   - `prophet gen`
5. Run 12 iterations of:
   - `prophet gen --skip-unchanged`
6. Collect mean/median/p95/min/max wall-clock timings.

Benchmark script:

1. `prophet-cli/scripts/benchmark_noop_generation.py`

## Environment

1. Platform: `linux`
2. Python: `3.14.2`
3. Iterations per mode: `12`

## Results

### `prophet gen`

1. Mean: `123.67 ms`
2. Median: `122.70 ms`
3. P95: `129.32 ms`
4. Min: `120.00 ms`
5. Max: `133.75 ms`

### `prophet gen --skip-unchanged`

1. Mean: `99.03 ms`
2. Median: `98.89 ms`
3. P95: `100.29 ms`
4. Min: `97.78 ms`
5. Max: `100.47 ms`

### Relative Improvement

1. Mean speedup factor: `1.25x`

## Conclusion

`--skip-unchanged` provides a measurable no-op speed improvement while preserving deterministic generation semantics and cache integrity.
