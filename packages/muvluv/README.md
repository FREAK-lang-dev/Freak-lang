# muvluv

`src/muvluv.fk` contains the Eishi/TSF declarations and explicit BETA,
YuukoLab and COSMO helper calls. Loading its declarations performs no output
or showcase setup. Call a helper explicitly to obtain its behavior.

The complete historical BETA Early Warning System is preserved as the
self-contained `examples/beta_early_warning.fk`. Its declarations are included
in that snapshot so moving it does not change its original execution inputs.
This move does not claim that every historical annotation or shape operation
is executable on both V3 backends.

The V3 regression assembles library source with a small consumer directly and
executes it through LLVM, including checks of the tier helper results. This
proves library initialization is silent; it does not claim that Hangar's pending
immutable package graph loader is complete. C shape execution and the broader
modular `muvluv::*` roadmap remain separate work.
