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

# Function to display dim blue color
def display_blue():
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 50))  # Dim blue color (R=0, G=0, B=50)
    strip.show()

# Display dim blue color
display_blue()

# Keep the blue color for 5 seconds
time.sleep(5)

# Turn off the LEDs
for i in range(strip.numPixels()):
    strip.setPixelColor(i, Color(0, 0, 0))  # Turn off LEDs
strip.show()
