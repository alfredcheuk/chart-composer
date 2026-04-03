#!/bin/bash
# process_chart.sh
#
# Saves the current clipboard image and composites it into branded chart PNGs.
#
# Usage:
#   1. Select the chart in Keynote and Cmd+C
#   2. Run: ./process_chart.sh "fund-name"
#
# The fund name is matched against chart_titles.json to get the branded title.
# Output goes to ./output/<fund-name>_dark.png and ./output/<fund-name>_transparent.png

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="/tmp/keynote-skill/keynote-chart-export"
TITLES_JSON="$SKILL_DIR/chart_titles.json"
FONT="$SKILL_DIR/assets/DINPro-Bold.otf"
COMPOSE="$SKILL_DIR/scripts/compose_chart.py"
OUTPUT_DIR="$SCRIPT_DIR/output"

if [ -z "$1" ]; then
  echo "Usage: $0 <fund-name>"
  echo ""
  echo "Available funds:"
  python3 -c "import json; [print(f'  - {k}') for k in json.load(open('$TITLES_JSON'))]"
  exit 1
fi

FUND_KEY="$1"

# Look up title from mapping (case-insensitive partial match)
TITLE=$(python3 -c "
import json, sys
titles = json.load(open('$TITLES_JSON'))
key = sys.argv[1].lower()
for k, v in titles.items():
    if key in k.lower() or k.lower() in key:
        print(v)
        sys.exit(0)
print('')
" "$FUND_KEY")

if [ -z "$TITLE" ]; then
  echo "ERROR: No title mapping found for '$FUND_KEY'"
  echo "Available funds:"
  python3 -c "import json; [print(f'  - {k}') for k in json.load(open('$TITLES_JSON'))]"
  exit 1
fi

# Derive kebab-case filename from fund key
SLUG=$(python3 -c "
import json, sys, re
titles = json.load(open('$TITLES_JSON'))
key = sys.argv[1].lower()
for k in titles:
    if key in k.lower() or k.lower() in key:
        print(re.sub(r'[^a-z0-9]+', '-', k.lower()).strip('-'))
        sys.exit(0)
" "$FUND_KEY")

echo "Fund:  $FUND_KEY"
echo "Title: $TITLE"
echo "Slug:  $SLUG"
echo ""

# Save clipboard to PNG
CHART_PNG="/tmp/chart_clipboard_$$.png"
echo "Saving clipboard to $CHART_PNG..."
pngpaste "$CHART_PNG"

if [ ! -f "$CHART_PNG" ]; then
  echo "ERROR: No image in clipboard. Copy a chart first (Cmd+C in Keynote)."
  exit 1
fi

echo "Clipboard saved."

# Scale up to target width if smaller
TARGET_WIDTH=1500
SCALED_PNG="/tmp/chart_scaled_$$.png"
python3 -c "
from PIL import Image
img = Image.open('$CHART_PNG')
w, h = img.size
target = $TARGET_WIDTH
if w < target:
    ratio = target / w
    new_w = target
    new_h = int(h * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    print(f'Scaled {w}x{h} → {new_w}x{new_h}')
else:
    print(f'Already {w}x{h}, no scaling needed')
img.save('$SCALED_PNG')
"
CHART_PNG="$SCALED_PNG"

echo "Composing..."

# Compose branded outputs
python3 "$COMPOSE" \
  --chart "$CHART_PNG" \
  --title "$TITLE" \
  --font "$FONT" \
  --output-dir "$OUTPUT_DIR"

# Rename with fund slug
mv "$OUTPUT_DIR/chart_dark.png" "$OUTPUT_DIR/${SLUG}_dark.png"
mv "$OUTPUT_DIR/chart_transparent.png" "$OUTPUT_DIR/${SLUG}_transparent.png"

echo ""
echo "Done!"
echo "  $OUTPUT_DIR/${SLUG}_dark.png"
echo "  $OUTPUT_DIR/${SLUG}_transparent.png"

# Cleanup
rm -f "$CHART_PNG"
