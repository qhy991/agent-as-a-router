# Held-out RangeSum Profile routing: verified analogy evidence

Route one GPT-5.6 Luna Worker per stage. There is no measured RangeSum outcome
or exact action table. Use only the following verified evidence from other
families:

- Generic task-shape routing was unreliable: a Luna Agent that mapped every
  local task to p000 and every system task to p100 scored only 4/12 stages.
- On RankCount and PrefixCount system tasks, repeated query batches sharing one
  input required reusable preprocessing outside the repeated target call.
- Supplying that verified shared-preprocessing mechanism with p100 produced
  3/3 correct, coordinated, performance-eligible Workers on both known tasks.
- Four of six families had no stable routing crossover, so do not infer that
  every many-batch task automatically benefits from p100.

Profiles are `neutral`, `p000`, and `p100`. Decision priority is correctness,
then performance feasibility, then complete token cost. Include these stages
in order:

1. `rangesum-p01`: one large batch of 1,200 range-sum queries over one input.
2. `rangesum-p02`: 20 batches of 60 range-sum queries sharing one input.

Choose by analogy without claiming that RangeSum has already been measured.
