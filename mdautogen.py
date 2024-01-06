import os
from subprocess import run


if not os.path.exists("docs"):
    os.mkdir("docs")

packages = ["dsdrive_api", "dsurl"]
for package in packages:
    with open(f"docs/{package}.md", "w") as file:
        run(["pydoc-markdown", "-p", package], stdout=file)
