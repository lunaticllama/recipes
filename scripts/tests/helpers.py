"""Test helpers: build Google Docs API JSON from a compact text snippet.

Snippet format (one paragraph per line):
  "## Title"      -> a HEADING_2 paragraph ("# " = HEADING_1, "### " = HEADING_3)
  "* text"        -> a paragraph that is part of a Docs list
  "\v" in a line  -> a soft line break (Shift+Enter), as the Docs API reports it
  "<text|url>"    -> a hyperlinked run of text
Everything else is a normal paragraph. A blank line is an empty paragraph.
"""
import os
import re
import sys
import textwrap

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

_LINK = re.compile(r"<([^|<>]*)\|([^<>]+)>")
_STYLES = {"# ": "HEADING_1", "## ": "HEADING_2", "### ": "HEADING_3"}


def _runs(text):
    runs, pos = [], 0
    for m in _LINK.finditer(text):
        if m.start() > pos:
            runs.append({"textRun": {"content": text[pos:m.start()], "textStyle": {}}})
        runs.append({"textRun": {"content": m.group(1),
                                 "textStyle": {"link": {"url": m.group(2)}}}})
        pos = m.end()
    if pos < len(text):
        runs.append({"textRun": {"content": text[pos:], "textStyle": {}}})
    return runs


def make_doc(snippet):
    """Return a dict shaped like the Docs API `documents.get` response."""
    content = [{"sectionBreak": {}}]
    for raw in textwrap.dedent(snippet).strip("\n").split("\n"):
        style, bullet = "NORMAL_TEXT", None
        m = re.match(r"(#{1,3})(?: |$)", raw)
        if m:
            style, raw = _STYLES[m.group(1) + " "], raw[m.end():]
        if raw.startswith("* "):
            bullet, raw = {"listId": "kix.test", "nestingLevel": 0}, raw[2:]
        runs = _runs(raw)
        if runs:
            runs[-1]["textRun"]["content"] += "\n"
        else:
            runs = [{"textRun": {"content": "\n", "textStyle": {}}}]
        para = {"elements": runs, "paragraphStyle": {"namedStyleType": style}}
        if bullet:
            para["bullet"] = bullet
        content.append({"paragraph": para})
    return {"documentId": "test", "title": "Test",
            "tabs": [{"documentTab": {"body": {"content": content}}}]}
