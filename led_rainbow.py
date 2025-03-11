import time
from rpi_ws281x import PixelStrip, Color

# LED strip configuration:
LED_COUNT      = 300      # Number of LED pixels
LED_PIN        = 12      # GPIO pin connected to the LEDs (GPIO 12, Pin 18)
LED_FREQ_HZ    = 800000 # Frequency of the PWM signal
LED_DMA        = 10     # DMA channel to use for PWM generation
LED_BRIGHTNESS = 50     # Dim brightness (0-255)
LED_INVERT     = False  # True to invert the signal
LED_CHANNEL    = 0

# Create an instance of the PixelStrip class
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# Function to generate a color based on the input position (0-255)
def wheel(pos):
    """Generate a color based on the input position (0-255)."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

# Function to create an indefinite rainbow cycle effect across the strip
def rainbow_cycle(wait_ms=20):
    """Move a rainbow across the LED strip indefinitely."""
    while True:  # Loop indefinitely
        for j in range(256):  # Run the rainbow cycle 256 times for a full rotation
            for i in range(strip.numPixels()):
                color = wheel((i + j) & 255)  # Apply the color wheel effect
                strip.setPixelColor(i, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)

# Run the rainbow cycle effect indefinitely
rainbow_cycle()
