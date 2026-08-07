# Per-product source registries

Optional layout (used by private CyberSource lane). If `registry/*.json` exists,
`content_bench.content_engine.registry.load_registry()` merges them.

Public content-bench still ships `data/content_engine/source_registry.json` as
the legacy fallback when `registry/` has no JSON product files.
