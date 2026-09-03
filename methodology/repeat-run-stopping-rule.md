# Repeat-run stopping rule

A repeated identical green run is not a default acceptance requirement.

Additional identical runs are justified when at least one of these is true:

1. the owning acceptance contract explicitly requires them;
2. the failure mechanism remains UNKNOWN;
3. behavior is stochastic/intermittent and another independent run measures residual risk;
4. the environment itself is being qualified and repetition is the evidence.

A deterministic, root-caused HARNESS or ENVIRONMENT issue that is structurally removed should re-enter its affected gate, but it does not automatically require repeated full-gate greens merely to accumulate a number.

> Repeat when repetition can falsify a live uncertainty. Stop when further identical execution would only accumulate green counts.
