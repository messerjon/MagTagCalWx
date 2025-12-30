"""
MagTag Calendar and Weather Display
Displays current date, day of week, weather icon, and temperature
Uses weather.gov (National Weather Service) API for weather data
"""

import time
import math
import os
import board
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_magtag.magtag import MagTag
import rtc
import socketpool
import wifi
import adafruit_ntp
import adafruit_imageload

# Initialize MagTag with status bar disabled
magtag = MagTag(default_bg=0xFFFFFF)  # White background, no default UI
magtag.peripherals.neopixel_disable = True  # Save power

# Load settings from settings.toml (CircuitPython 10.x way)
def get_setting(key, default=None):
    """Get a setting from settings.toml via os.getenv"""
    value = os.getenv(key)
    return value if value is not None else default

# Screen dimensions: 296x128 pixels
SCREEN_WIDTH = 296
SCREEN_HEIGHT = 128

# Color definitions for e-ink display
BLACK = 0x000000
WHITE = 0xFFFFFF

def get_weather_data():
    """
    Fetch weather data from weather.gov (National Weather Service) API
    Returns dict with temperature (high, low) and weather condition
    Note: weather.gov only provides data for US locations
    """
    try:
        # Get location from settings.toml (latitude and longitude)
        latitude = get_setting("LATITUDE", "47.6062")  # Seattle default
        longitude = get_setting("LONGITUDE", "-122.3321")
        
        # Validate coordinates
        try:
            lat_float = float(latitude)
            lon_float = float(longitude)
            if not (-90 <= lat_float <= 90) or not (-180 <= lon_float <= 180):
                raise ValueError("Coordinates out of valid range")
        except (ValueError, TypeError):
            latitude = "47.6062"
            longitude = "-122.3321"

        # Step 1: Get the forecast grid endpoint for this location
        points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        
        points_response = magtag.network.fetch(points_url)
        points_data = points_response.json()
        
        # Step 2: Get the forecast URL from the points data
        if "properties" not in points_data or "forecast" not in points_data["properties"]:
            raise ValueError("Invalid response from points API")
        
        forecast_url = points_data["properties"]["forecast"]
        
        # Step 3: Fetch the actual forecast
        forecast_response = magtag.network.fetch(forecast_url)
        forecast_data = forecast_response.json()
        
        # Validate forecast data structure
        if "properties" not in forecast_data or "periods" not in forecast_data["properties"]:
            raise ValueError("Invalid response from forecast API")
        
        periods = forecast_data["properties"]["periods"]
        if not periods or len(periods) == 0:
            raise ValueError("No forecast periods available")
        
        # Get today's forecast (first period)
        today_forecast = periods[0]

        # weather.gov provides temperatures in Fahrenheit
        # Find daytime high and nighttime low
        temp_high = "--"
        temp_low = "--"
        condition = "Unknown"

        for period in periods[:4]:  # Check first 4 periods
            if period.get("isDaytime", False):
                if temp_high == "--":
                    temp_high = period.get("temperature", "--")
                    condition = period.get("shortForecast", "Unknown")
            else:
                if temp_low == "--":
                    temp_low = period.get("temperature", "--")

        # Fallback if we didn't find proper day/night periods
        if temp_high == "--":
            temp_high = periods[0].get("temperature", "--")
            condition = periods[0].get("shortForecast", "Unknown")
        if temp_low == "--":
            temp_low = temp_high

        return {
            "temp_high": temp_high,
            "temp_low": temp_low,
            "condition": condition,
            "units": "°F"  # weather.gov always returns Fahrenheit
        }
    except Exception:
        return {
            "temp_high": "--",
            "temp_low": "--",
            "condition": "Unknown",
            "units": "°F"
        }

def get_weather_icon_type(condition):
    """
    Return weather icon type based on condition
    Maps weather.gov shortForecast descriptions to icon types
    """
    condition_lower = condition.lower()

    if "sunny" in condition_lower or "clear" in condition_lower:
        return "sun"
    elif "rain" in condition_lower or "shower" in condition_lower or "drizzle" in condition_lower:
        return "rain"
    elif "thunder" in condition_lower or "storm" in condition_lower:
        return "storm"
    elif "snow" in condition_lower or "flurr" in condition_lower:
        return "snow"
    elif "fog" in condition_lower or "mist" in condition_lower or "haze" in condition_lower:
        return "fog"
    elif "wind" in condition_lower:
        return "wind"
    elif "cloud" in condition_lower or "overcast" in condition_lower or "partly" in condition_lower or "mostly" in condition_lower:
        return "cloud"
    else:
        return "unknown"

def load_weather_icon(icon_type, x, y):
    """
    Load a weather icon BMP file and return a displayio.Group
    Icons are 100x100 pixel 1-bit BMPs
    """
    icon_group = displayio.Group(x=x, y=y)

    # Map icon type to filename
    icon_files = {
        "sun": "/icons/icon_sun.bmp",
        "cloud": "/icons/icon_cloud.bmp",
        "rain": "/icons/icon_rain.bmp",
        "snow": "/icons/icon_snow.bmp",
        "storm": "/icons/icon_storm.bmp",
        "fog": "/icons/icon_fog.bmp",
        "wind": "/icons/icon_wind.bmp",
        "unknown": "/icons/icon_unknown.bmp",
    }

    filename = icon_files.get(icon_type, "/icons/icon_unknown.bmp")

    try:
        icon_bitmap, icon_palette = adafruit_imageload.load(
            filename, bitmap=displayio.Bitmap, palette=displayio.Palette
        )
        tile_grid = displayio.TileGrid(icon_bitmap, pixel_shader=icon_palette)
        icon_group.append(tile_grid)
    except Exception:
        # Fallback: create a simple placeholder
        placeholder = displayio.Bitmap(100, 100, 2)
        palette = displayio.Palette(2)
        palette[0] = WHITE
        palette[1] = BLACK
        # Draw X
        for i in range(100):
            placeholder[i, i] = 1
            placeholder[99 - i, i] = 1
        tile_grid = displayio.TileGrid(placeholder, pixel_shader=palette)
        icon_group.append(tile_grid)

    return icon_group

def create_display():
    """Create the display layout with date, weather, and temperature"""

    # Clear any existing display
    splash = displayio.Group()

    # Add white background
    color_bitmap = displayio.Bitmap(SCREEN_WIDTH, SCREEN_HEIGHT, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = WHITE
    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)
    
    # Get current time
    current_time = time.localtime()
    
    # Month names
    months = ["", "January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    
    # Day names
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Format date components
    month_name = months[current_time.tm_mon]
    day_name = days[current_time.tm_wday]
    date_num = current_time.tm_mday
    
    # Get weather data
    weather = get_weather_data()
    weather_icon_type = get_weather_icon_type(weather["condition"])
    
    # LEFT SECTION: Date and Day
    # Month name (top left) - full name
    month_label = label.Label(
        terminalio.FONT,
        text=month_name.upper(),
        color=BLACK,
        scale=2,
        x=5,
        y=12
    )
    splash.append(month_label)

    # Date number (large, left side)
    date_label = label.Label(
        terminalio.FONT,
        text=str(date_num),
        color=BLACK,
        scale=6,
        x=5,
        y=60
    )
    splash.append(date_label)

    # Day of week (bottom left) - full name
    day_label = label.Label(
        terminalio.FONT,
        text=day_name.upper(),
        color=BLACK,
        scale=2,
        x=5,
        y=115
    )
    splash.append(day_label)
    
    # MIDDLE SECTION: Weather Icon (100x100 BMP)
    # Position icon to fit - display is 296x128, icon is 100x100
    icon_x = 110  # Centered in middle area
    icon_y = 14   # Vertically centered (128 - 100) / 2 = 14

    # Load weather icon from BMP file
    weather_icon = load_weather_icon(weather_icon_type, icon_x, icon_y)
    splash.append(weather_icon)

    # Weather condition text at bottom of screen (below the icon area)
    condition_text = weather["condition"]
    condition_label = label.Label(
        terminalio.FONT,
        text=condition_text[:16],  # Truncate if too long
        color=BLACK,
        x=icon_x,
        y=120
    )
    splash.append(condition_label)

    # RIGHT SECTION: Temperature - just numbers, stacked, larger
    # High temperature (top)
    high_label = label.Label(
        terminalio.FONT,
        text=str(weather['temp_high']),
        color=BLACK,
        scale=4,
        x=SCREEN_WIDTH - 55,
        y=35
    )
    splash.append(high_label)

    # Low temperature (bottom)
    low_label = label.Label(
        terminalio.FONT,
        text=str(weather['temp_low']),
        color=BLACK,
        scale=4,
        x=SCREEN_WIDTH - 55,
        y=90
    )
    splash.append(low_label)
    
    # Display the layout
    board.DISPLAY.root_group = splash

    # Force display refresh for e-ink (wait for display to be ready)
    while board.DISPLAY.time_to_refresh > 0:
        time.sleep(0.5)
    board.DISPLAY.refresh()
    while board.DISPLAY.busy:
        pass


def seconds_until_midnight():
    """Calculate seconds until next midnight"""
    now = time.localtime()
    # Seconds since midnight
    seconds_today = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
    # Seconds in a day minus seconds since midnight
    return 86400 - seconds_today

def main():
    """Main function to run the MagTag calendar display"""

    # Connect to WiFi
    try:
        magtag.network.connect()
    except Exception:
        pass  # Continue with placeholder data if WiFi fails

    # Sync time using NTP (no Adafruit IO needed)
    try:
        pool = socketpool.SocketPool(wifi.radio)
        ntp = adafruit_ntp.NTP(pool, tz_offset=-8)  # PST = UTC-8
        rtc.RTC().datetime = ntp.datetime
    except Exception:
        pass  # Use device time if NTP fails

    # Create and show the display
    create_display()

    # Calculate seconds until midnight and sleep until then
    sleep_seconds = seconds_until_midnight()
    magtag.exit_and_deep_sleep(sleep_seconds)

# Run the main function
if __name__ == "__main__":
    main()
