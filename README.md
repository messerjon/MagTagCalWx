# MagTag Calendar & Weather Display

A calendar and weather display for the Adafruit MagTag e-ink display. Shows the current date, day of week, weather icon, and high/low temperatures.

## Features

- Large, easy-to-read date display
- Cartoon-style weather icons
- High and low temperature display
- Automatically updates at midnight
- Low power - uses deep sleep between updates

## Requirements

### Hardware
- [Adafruit MagTag](https://www.adafruit.com/product/4800)

### Software
- CircuitPython 10.x
- Required libraries (installed via circup)

## Important Note

**This project uses the National Weather Service (weather.gov) API, which only provides weather data for US locations.** International users would need to modify the code to use a different weather API.

## Installation

### 1. Install CircuitPython

Make sure your MagTag is running CircuitPython 10.x. Download from:
https://circuitpython.org/board/adafruit_magtag_2.9_grayscale/

### 2. Install Required Libraries

Install `circup` if you haven't already:
```bash
pip install circup
```

With your MagTag connected via USB, install the required libraries:
```bash
circup install adafruit_magtag adafruit_ntp adafruit_imageload
```

Or install all dependencies automatically:
```bash
circup install --auto
```

### 3. Copy Files to MagTag

Copy all project files to your MagTag's CIRCUITPY drive:
```bash
cp code.py /Volumes/CIRCUITPY/
cp icon_*.bmp /Volumes/CIRCUITPY/
```

### 4. Configure Settings

Copy the example settings file and edit with your information:
```bash
cp settings.toml.example /Volumes/CIRCUITPY/settings.toml
```

Edit `settings.toml` on the CIRCUITPY drive with your:
- WiFi network name and password
- Latitude and longitude (US locations only)

Find your coordinates at: https://www.latlong.net/

### 5. Reset the MagTag

Press the reset button. The display should connect to WiFi, fetch weather data, and show your calendar!

## Customization

### Timezone

The NTP time sync uses a hardcoded timezone offset in `code.py`. Find this line and adjust for your timezone:
```python
ntp = adafruit_ntp.NTP(pool, tz_offset=-8)  # PST = UTC-8
```

Common offsets:
- PST (Pacific): -8
- MST (Mountain): -7
- CST (Central): -6
- EST (Eastern): -5

Note: This does not auto-adjust for daylight saving time.

## Weather Icons

The display uses cartoon-style weather icons from the [Gartoon Weather icon set](https://www.iconarchive.com/show/gartoon-weather-icons-by-gartoon-team.html) (GPL licensed).

Icons included:
- Sun (clear/sunny)
- Cloud (cloudy/overcast)
- Rain (rain/showers)
- Snow (snow/ice)
- Storm (thunderstorm)
- Fog (fog/haze)
- Wind
- Unknown (fallback)

## Troubleshooting

### Display shows "--" for temperatures
- Check WiFi credentials in `settings.toml`
- Verify your coordinates are within the US
- Check that weather.gov API is accessible

### Wrong date/time
- Ensure WiFi is connected (needed for NTP time sync)
- Adjust timezone offset in code.py

### Libraries not found
Run `circup install --auto` to install missing dependencies.

## License

MIT License - See LICENSE file

Weather icons: GPL (Gartoon Weather by Gartoon Team)
