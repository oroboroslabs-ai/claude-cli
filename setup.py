from setuptools import setup, find_packages

setup(
    name="claude-cli",
    version="1.0.0",
    description="claude — Sovereign Terminal AI Assistant (Oroboros Core) — Hardened",
    author="Oroboros Labs",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.3",
        "lxml>=4.9.1",
        "PyYAML>=6.0.1",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "claude=claude_o_cli.claude_o_cli:main",
        ],
    },
)