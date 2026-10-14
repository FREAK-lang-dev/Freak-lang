# Deferred V3.5 V4 loop contracts

These four fixtures and their complete executable expectations are preserved
for the local V3.5 while/counted-loop implementation through b8c5e99. The current
locked V4 baseline is the unchanged official b43127c source, which does not
implement those additions. They are not active positive conformance gates for
that baseline. The shipping V3 loop tests remain active.

The root test directory is the active fixture inventory in check_v4.py. Restore
these fixtures and smokes.json registrations only together with their matching
V4 semantic implementation, after verifying all frontend, MIR, Meiya, restore,
and native execution expectations. Referenced examples remain under
src/compiler/v4/examples; none of this preservation marks the deferred feature
as passing or complete.
