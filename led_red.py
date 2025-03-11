import time
from rpi_ws281x import PixelStrip, Color

LED_COUNT = 300 # LED strip configuration:
LED_PIN        = 12      # GPIO pin connected to the LEDs (GPIO 12, Pin 18)
LED_FREQ_HZ    = 800000 # Frequency of the PWM signal
LED_DMA        = 10     # DMA channel to use for PWM generation
LED_BRIGHTNESS = 50     # Dim brightness (0-255)
LED_INVERT     = False  # True to invert the signal
LED_CHANNEL    = 0

# Create an instance of the PixelStrip class
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# Set all LEDs to dim red color
def display_red():
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(50, 0, 0))  # Dim red color (R=50, G=0, B=0)
    strip.show()

# Display dim red color
display_red()

# Keep the red color for 5 seconds
time.sleep(5)

# Turn off the LEDs
for i in range(strip.numPixels()):
    strip.setPixelColor(i, Color(0, 0, 0))  # Turn off LEDs
strip.show()
