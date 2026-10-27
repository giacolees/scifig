# Architecture diagram skill forward test

This is a local workflow test of `skills/scientific-figures/SKILL.md`, not a live
Codex or Claude skill-discovery test. The test used the available terminal, the
repository virtual environment, and an image viewer. It followed the skill and
`docs/diagrams.md` from a realistic request to depict the function:

```python
def forward(x):
    z = encoder(x)
    h = decoder(z)
    return head(h + z)
```

The source file, YAML, reproducible Python rendering code, PDF, SVG, PNG,
resolved YAML, and layout JSON were retained under
`/tmp/scifig-diagram-skill-check/`. The YAML is the diagram source; `render.py`
provides an equivalent Python entry point. Using the repository virtual
environment's executables, the commands from the isolated directory were:

```sh
scifig validate diagram.yaml
scifig render diagram.yaml
python render.py
```

The isolated environment used scifig 0.2.0, Python 3.12.2, Matplotlib 3.11.2,
and Graphviz dot 14.0.2. All five output files were nonempty. The PDF and SVG
are vector exports; the PNG is the preview. The sidecar records layout and
renderer versions. Validation and rendering both reported that the addition's
shape cannot be checked with missing dimensions. No dimensions were invented.

The CLI render and the equivalent Python reproduction were run, for two renders total; the actual PNG was inspected after each. It shows x entering the
encoder; z splitting to the decoder and directly to Add; h joining z at Add;
and the sum entering the head and output. Labels, arrows, and the skip path
were legible, with no visible clipping or overlap. The figure is explicitly
illustrative and the warning remains a caveat: this workflow does not infer
or verify tensor shapes or the model architecture from code automatically.
