# claude-o-cli package
# ∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST
# vA.1272 — ZTA Active — RGE Governing

__version__ = "1.0.0"


def main():
    """Entry point for the claude console command — launches hardened server."""
    import sys
    import os
    # Parse CLI args
    args = sys.argv[1:]
    model_override = None
    for i, a in enumerate(args):
        if a.startswith('--model='):
            model_override = a.split('=', 1)[1]
        elif a == '--model' and i + 1 < len(args):
            model_override = args[i + 1]
    # Change to the package directory so relative imports work
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(pkg_dir)
    if pkg_dir not in sys.path:
        sys.path.insert(0, pkg_dir)
    # Import and run the hardened server
    from run_cli import app, DEFAULT_MODEL
    if model_override:
        import run_cli as _r
        _r.DEFAULT_MODEL = model_override
    print(f"  GUI:     http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)