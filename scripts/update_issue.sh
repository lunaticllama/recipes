#!/usr/bin/env bash
# Open, update or close the "Recipe doc check" GitHub issue from a report file
# written by `sync.py --report-md`. An empty report means the check is clean.
#
# Usage: scripts/update_issue.sh REPORT.md
# Needs the gh CLI with GH_TOKEN allowed to write issues (the workflows set this up).
#
# GitHub emails about new issues and new comments, not about edits, so a changed
# report is posted as a comment as well as replacing the issue text. Nights with
# no change touch nothing and send nothing.
set -euo pipefail

REPORT="$1"
TITLE="Recipe doc check"
TODAY=$(date -u +%Y-%m-%d)

num=$(gh issue list --state open --limit 100 --json number,title \
        --jq ".[] | select(.title == \"$TITLE\") | .number" | head -n1)

if [ -s "$REPORT" ]; then
  if [ -z "$num" ]; then
    gh issue create --title "$TITLE" --body-file "$REPORT"
    echo "Opened the \"$TITLE\" issue."
    exit 0
  fi
  current=$(gh issue view "$num" --json body --jq .body | tr -d '\r')
  if [ "$current" = "$(tr -d '\r' < "$REPORT")" ]; then
    echo "Report unchanged; issue #$num left as it is."
    exit 0
  fi
  gh issue edit "$num" --body-file "$REPORT"
  {
    echo "The report changed on $TODAY. Latest version:"
    echo
    cat "$REPORT"
  } > "$REPORT.comment"
  gh issue comment "$num" --body-file "$REPORT.comment"
  echo "Updated issue #$num."
else
  if [ -n "$num" ]; then
    gh issue close "$num" --comment "The doc check is clean as of $TODAY, so this is closed. It reopens as a new issue if something comes up."
    echo "Closed issue #$num."
  else
    echo "The doc check is clean; no issue needed."
  fi
fi
