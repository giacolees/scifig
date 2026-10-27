"""Built-in figure families sharing the same rendering contract."""

from scifig.core.registry import register_template
from scifig.templates import ablation, benchmark, distribution, heatmap, learning_curve

for _name, _module in (
    ("learning_curve", learning_curve),
    ("benchmark", benchmark),
    ("ablation", ablation),
    ("distribution", distribution),
    ("heatmap", heatmap),
):
    register_template(_name, _module.draw, data_family=_name)
