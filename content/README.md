# Generated content

Approved markdown pages live here. The portal, MCP server, humanizer, and evals read from `content/` and `normalized/` only.

Pages are generated (A2 / Connect proof), then optionally passed through
`pipelines/write_prose.py` and `pipelines/humanize.py` (A3). Prose lives in
`<!-- section:prose -->` blocks; templated facts live in `<!-- section:facts -->`
and are protected by `fact_hash` — the humanizer cannot change them.

Do not hand-paste integration prose into JS modules. Do not serve from `raw/`.
