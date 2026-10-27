"""Diagram diagnostics catch layout conflicts requiring review."""

import warnings

from scifig.diagrams.rendering import check_diagram_visual, render_diagram
from scifig.diagrams.specs import DiagramSpec


def draw(nodes, edges=()):
    spec = DiagramSpec.model_validate({"layout": "manual", "nodes": nodes, "edges": list(edges)})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return render_diagram(spec)


def test_diagnostics_flag_overlapping_nodes_and_edges_through_other_nodes():
    result = draw(
        {
            "a": {"label": "A", "position": [0, 0]},
            "b": {"label": "B", "position": [4, 0]},
            "obstacle": {"label": "Obstacle", "position": [2, 0]},
            "overlap": {"label": "Overlap", "position": [2, 0]},
        },
        [{"source": "a", "target": "b"}],
    )
    messages = check_diagram_visual(result)
    assert any("overlap" in message.lower() and "obstacle" in message for message in messages)
    assert any("crosses node" in message and "obstacle" in message for message in messages)
    assert any("crosses node" in message for message in result.diagnostics)


def test_diagnostics_flag_label_that_does_not_fit():
    result = draw(
        {
            "a": {
                "label": "Supercalifragilisticexpialidocious",
                "position": [0, 0],
                "size": [0.3, 0.3],
            }
        }
    )
    assert any("label does not fit" in message for message in result.diagnostics)


def test_default_feedback_loop_stays_outside_its_node():
    result = draw(
        {"state": {"label": "State", "position": [0, 0]}},
        [{"source": "state", "target": "state", "kind": "feedback"}],
    )
    assert not any("crosses node" in message for message in result.diagnostics)
