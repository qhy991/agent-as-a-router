# Twelve-stage Profile routing plan: task structure only

Route one GPT-5.6 Luna Worker per stage. You have no measured outcome table.

Profiles:

- `neutral`: no behavioral Profile; unconstrained implementation search.
- `p000`: local, bounded-information, direct implementation behavior.
- `p100`: coordinated multi-module implementation behavior.

Decision priority is correctness, then performance feasibility, then complete
token cost. A low-token action is invalid if it misses the performance target.

Stages:

1. `rankcount-local`: rank-count queries in one large query batch.
2. `rankcount-system`: rank-count queries in 25 small batches sharing one input.
3. `membership-local`: exact-membership queries in one large batch.
4. `membership-system`: exact-membership queries in 25 batches sharing one input.
5. `categorysum-local`: category-sum queries in one large batch.
6. `categorysum-system`: category-sum queries in 25 batches sharing one input.
7. `anagram-local`: anagram-frequency queries in one large batch.
8. `anagram-system`: anagram-frequency queries in 25 batches sharing one input.
9. `rangemin-local`: repeated range-minimum queries in one large batch.
10. `rangemin-system`: range-minimum queries in 25 batches sharing one input.
11. `prefixcount-local`: string-prefix-count queries in one large batch.
12. `prefixcount-system`: string-prefix-count queries in 25 batches sharing one input.
