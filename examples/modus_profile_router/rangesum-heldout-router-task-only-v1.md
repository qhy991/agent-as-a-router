# Held-out RangeSum Profile routing: task structure only

Route one GPT-5.6 Luna Worker per stage. You have no RangeSum outcome data.

Profiles:

- `neutral`: no behavioral Profile; unconstrained implementation search.
- `p000`: local, bounded-information, direct implementation behavior.
- `p100`: coordinated multi-module implementation behavior.

Decision priority is correctness, then performance feasibility, then complete
token cost. Include these stages in order:

1. `rangesum-p01`: one large batch of 1,200 range-sum queries over one input.
2. `rangesum-p02`: 20 batches of 60 range-sum queries sharing one input.

No measured RangeSum Profile action or mechanism label is available.
