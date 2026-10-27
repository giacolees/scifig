# Contributing

Install the project and development dependencies with `python -m pip install -e '.[dev]'`. Run `pytest` and `ruff check .` before submitting a change. Run `python examples/make_gallery.py` and inspect the affected PNGs when changing rendering, labels, styles, or exports. Gallery data is synthetic and must remain clearly labeled as such.

## Adding a figure family

Add a callable template and register it with `scifig.core.registry.register_template(name, callable, data_family="learning_curve")`, selecting the existing data family whose contract it uses. It should accept an Axes, the validated prepared table, the figure spec, and resolved style (in that order); draw on the supplied Axes without mutating the source table or global plotting state. Extend semantic validation and the spec only for the new family's actual requirements. Document its long-table contract and any aggregation or uncertainty semantics. Add focused tests for valid inputs, meaningful invalid inputs, and rendering/export behavior, and include a synthetic example where useful. Keep shared styling, annotations, diagnostics, and export in the common engine rather than duplicating them in a template.

The registry is deliberately small and callable-based; it is not a plugin framework. Preserve strict validation, explicit aggregation, and reproducible outputs. External reference repositories are background research, not sources of vendored code; see [research](research.md).
