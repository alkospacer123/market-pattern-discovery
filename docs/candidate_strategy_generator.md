# Candidate Strategy Generator

The Phase 6A candidate generator is a deterministic expansion of the frozen
strategy-family registry. It is an **architecture tool**, not a discovery,
ranking, optimization, backtest, or trading-execution component.

## Safety boundary

`generate_candidates` accepts only the result-free Phase 6A registry, a fixed
seed, a code-version identifier, and explicit enumeration limits. It has no
market-data input and does not accept outcomes, performance metrics, profit
factor, or 2025 TRUE OOS data. It neither reads files nor invokes the simulator.

Before expansion, the generator:

1. requires `phase == "6A"` and `real_results_included == false`;
2. verifies every family fingerprint and preregistration flag; and
3. checks per-family and global candidate-count limits without truncation.

Families, instruments, timeframes, and parameter names are sorted. Parameter
values retain the order preregistered in each allowed domain. A candidate ID is
derived from its family, parameters, instrument, timeframe, seed, and code
version. The full emitted record also receives a canonical SHA-256 fingerprint.
The same inputs therefore produce byte-equivalent records in the same order.

## Example

```python
import json
from pathlib import Path

from market_pattern_discovery.strategy_discovery.candidate_generator import (
    generate_candidates,
)

registry = json.loads(
    Path("config/phase6a/strategy_candidate_registry_v1.json").read_text()
)
candidates = generate_candidates(registry, seed=617, code_version="<git-sha>")
```

Generated records remain hypotheses. Generation does not promote or freeze a
candidate and provides no evidence of predictive or economic value.
