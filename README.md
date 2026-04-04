# Chart Composer

A Streamlit web app that composites fund chart images into branded PNG outputs ready for web use.

## What it does

Takes a chart image and a fund name, and produces two branded PNG files:

1. **Dark version** -- chart on a `#2A2E3C` background with 30px rounded corners
2. **Transparent version** -- chart on a transparent background (no rounded corners)

Both versions include:
- Chart title centered at the top in DINPro Bold (36px, white)
- 80px margin around all content
- Chart scaled up to 1500px wide (if smaller) using Lanczos resampling

## How to use

1. Open the fund's Keynote file
2. Right-click the chart and copy it
3. Open the app and click **Paste chart from clipboard**
4. Select the fund from the dropdown (the title auto-fills from the mapping)
5. Click **Compose**
6. Download the dark version, transparent version, or both as a zip

You can also toggle "Upload a file instead" to upload a chart PNG/JPEG directly.

## Fund title mapping

The app maps fund names to chart titles via `chart_titles.json`:

| Fund | Chart title |
|------|-------------|
| Liquid Alpha Fund of Funds | Positioned for Next Phase of the Bull Cycle |
| Aspen Coinbase Bitcoin Yield Feeder Fund | Cumulative Net Performance (%) |
| Aspen Market Neutral Yield Fund | Cumulative Net Returns |
| Aspen Yield Opportunities Fund | Growth of 1 BTC - Cumulative Net Performance |

To add or update a mapping, edit `chart_titles.json` and push.

## CLI alternative

For local use on macOS, `process_chart.sh` saves the clipboard image and composes directly:

```bash
# Copy a chart in Keynote (Cmd+C), then:
./process_chart.sh "yield opportunities"
```

Requires `pngpaste` (`brew install pngpaste`) and Pillow.

## Local development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

Deployed on [Streamlit Cloud](https://streamlit.io/cloud). Any push to `main` auto-redeploys.

## Project structure

```
app.py                 # Streamlit web app
chart_titles.json      # Fund name -> chart title mapping
process_chart.sh       # CLI alternative (macOS only)
requirements.txt       # Python dependencies
assets/
  DINPro-Bold.otf      # Brand font for title rendering
```
