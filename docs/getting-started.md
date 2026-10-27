# Getting started

Install from the project root with `python -m pip install -e .`, then run `python examples/make_gallery.py`. The five example tables are **synthetic**: their numbers are invented for demonstration and are not research results. The scripts work from any current directory; YAML data and export paths are resolved relative to the YAML file.

For a Python example, run `python examples/python_api.py`. It produces the same learning curve as `examples/specs/learning_curve.yaml`: the line is the mean of three synthetic runs and the band is one sample standard deviation. Save the script and source data alongside your own outputs so they can be reproduced.

Tables use long format. Learning curves require numeric x and y; benchmarks and ablations use categorical x and numeric y; distributions retain raw observations; heatmaps require categorical x and y and one numeric value per cell in a complete grid. Optional groups apply to learning curves and benchmarks. Use `aggregate: mean` or `median` only when justified; the default is no aggregation. Sample `std`, `sem`, and `ci95` require at least two observations per cell. The `ci95` normal approximation has assumptions that must be evaluated for the study; supplied lower and upper columns are absolute endpoints. No smoothing is performed.

Inspect the PNG at its intended size, review diagnostics, and verify scientific semantics and venue requirements yourself. Presets are editable starting points, not guarantees of venue compliance. PDF and SVG retain vector artists, while PNG is a convenient preview. See [the gallery](gallery.md) and [architecture](architecture.md).

## Agent skill

The repository includes [`skills/scientific-figures/SKILL.md`](../skills/scientific-figures/SKILL.md). Make it discoverable using your agent's skill installation conventions. For example:

- **Codex:** copy the skill directory to `.agents/skills/scientific-figures` in your project, then request `$scientific-figures` with your data and research objective. Repository discovery and explicit invocation follow the [official OpenAI skill documentation](https://learn.chatgpt.com/docs/build-skills).
- **Claude Code:** copy the skill directory to `.claude/skills/scientific-figures` in your project, then invoke `/scientific-figures` with the task, following the [Claude Code skill documentation](https://code.claude.com/docs/en/skills).

The skill directs the agent to inspect actual inputs, preserve reproducible sources, inspect a rendered preview, and stop after at most three renders.
