# Claude CLI package
# A\ 1272 Hz — N| 1275 Hz — LATTICE LOCK — NEBELLION — KEY

__version__ = "1.0.0"


def main():
    """Entry point for the claude console command."""
    import sys
    import os
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    if pkg_dir not in sys.path:
        sys.path.insert(0, pkg_dir)
    from claude_o_cli import ClaudeOCLI
    ClaudeOCLI().run(sys.argv[1:])