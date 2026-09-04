#!/bin/bash

echo "INSTANA_URL: $INSTANA_URL"
echo "INSTANA_KEY: $INSTANA_KEY"

set -e

echo "Starting Instana injection process"

if [[ -z "$INSTANA_URL" || -z "$INSTANA_KEY" ]]; then
  echo "Instana environment variables not set. Skipping injection."
  exit 0
fi

echo "Finding index.html"

INDEX_HTML="./dist/index.html"

if [ ! -f "$INDEX_HTML" ]; then
  echo "Error: index.html not found at $INDEX_HTML"
  echo "PWD: $(pwd)"
  echo "Contents of ./dist:"
  ls -l ./dist || echo "(dist directory missing)"
  exit 1
fi

echo "Found index.html"

INSTANA_SCRIPT=$(mktemp)
cat > "$INSTANA_SCRIPT" <<EOF
  <script>
    (function(s,t,a,n){s[t]||(s[t]=a,n=s[a]=function(){n.q.push(arguments)},
    n.q=[],n.v=2,n.l=1*new Date)})(window,"InstanaEumObject","ineum");

    ineum('reportingUrl', '${INSTANA_URL}');
    ineum('key', '${INSTANA_KEY}');
    ineum('trackSessions');
  </script>
  <script defer crossorigin="anonymous" src="static/scripts/eum.min.js"></script>
EOF

echo "Injecting Instana script into $INDEX_HTML"

awk -v script="$(cat "$INSTANA_SCRIPT")" '
  /<head>/ {
    print;
    print script;
    next
  }
  { print }
' "$INDEX_HTML" > "$INDEX_HTML.tmp" && mv "$INDEX_HTML.tmp" "$INDEX_HTML"

rm "$INSTANA_SCRIPT"

echo "Instana script injected successfully."
