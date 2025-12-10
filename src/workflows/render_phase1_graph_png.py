"""
Render Phase 1 LangGraph workflow to a PNG image.

Usage:
    python render_phase1_graph_png.py
"""

import os
import logging

from phase1_workflow_langgraph import create_phase1_graph

# Optional: if you want to force local rendering via Pyppeteer instead of mermaid.ink
try:
    from langchain_core.runnables.graph_mermaid import MermaidDrawMethod
except ImportError:
    MermaidDrawMethod = None  # Fallback if not available


logger = logging.getLogger("Phase1GraphRenderer")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def save_phase1_graph_png(
    output_path: str = "phase1_graph.png",
    use_pyppeteer: bool = False,
) -> str:
    """
    Generate a PNG image of the Phase 1 LangGraph workflow.

    Args:
        output_path: File path to save the PNG.
        use_pyppeteer: If True, render locally via Pyppeteer instead of mermaid.ink API
                       (requires `MermaidDrawMethod` to be importable).

    Returns:
        The absolute path to the saved PNG file.
    """
    logger.info("Creating Phase 1 graph...")
    graph = create_phase1_graph()

    logger.info("Rendering graph to PNG...")
    graph_obj = graph.get_graph()

    if use_pyppeteer and MermaidDrawMethod is not None:
        img_bytes = graph_obj.draw_mermaid_png(
            draw_method=MermaidDrawMethod.PYPPETEER
        )
    else:
        # Default: use mermaid.ink API via LangGraph
        img_bytes = graph_obj.draw_mermaid_png()

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(img_bytes)

    abs_path = os.path.abspath(output_path)
    logger.info(f"✅ Graph PNG saved to: {abs_path}")
    return abs_path


if __name__ == "__main__":
    # Change output_path if you want a different filename or folder
    save_phase1_graph_png(output_path="phase1_graph.png", use_pyppeteer=False)
