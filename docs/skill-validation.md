# Scientific-figures skill validation

An independent agent followed the repository skill for a request to compare DAgger, AggreVaTe and BC using the explicitly synthetic `examples/data/learning_curve.csv`. The working directory was `/tmp/scifig-skill-check`; it contains a copy of the CSV, standalone `figure.yaml`, `reproduce.py`, `README.md`, dependency versions and PDF/SVG/PNG outputs. These are invented teaching data, not research results.

The table has three runs for each method and iteration. The specification requests the mean and sample standard deviation at each iteration. The agent ran the following from the repository root, using the repository's UV environment:

```sh
.venv/bin/python -m scifig validate /tmp/scifig-skill-check/figure.yaml
.venv/bin/python -m scifig render /tmp/scifig-skill-check/figure.yaml
.venv/bin/python /tmp/scifig-skill-check/reproduce.py
```

Validation succeeded. Two renders were performed: one via the CLI and one via the Python reproduction script, within the skill's three-render limit. Both emitted the scientific warning that independence of observations cannot be assumed. Checkpoints from the same run are repeated observations; the standard-deviation bands are descriptive, not confidence intervals. The rendered PNG was visually inspected: the outside legend, category names, axes, units, synthetic label and intervals were visible without apparent clipping or overlap. Line styles and markers distinguish the methods in addition to color. This review cannot establish scientific validity or venue compliance.

Python 3.12.2, scifig 0.1.0, Matplotlib 3.11.2, NumPy 2.5.4, pandas 3.1.0, Pydantic 2.14.1 and PyYAML 6.0.3 were used. This exercised the skill instructions in an isolated agent task; it did not test live Codex or Claude Code product integration or skill discovery. `/tmp` is temporary and may be cleared by the host.
