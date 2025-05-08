import time
import numpy as np
import pyaudio
from rpi_ws281x import PixelStrip, Color
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# LED strip configuration:
LED_COUNT      = 300      # Number of LED pixels
CENTER_LEFT    = 149
CENTER_RIGHT   = 150
LED_PIN        = 12       # GPIO pin connected to the LEDs (GPIO 12, Pin 18)
LED_FREQ_HZ    = 800000   # Frequency of the PWM signal
LED_DMA        = 10       # DMA channel to use for PWM generation
LED_BRIGHTNESS = 200      # Default brightness (0-255)
LED_INVERT     = False    # True to invert the signal
LED_CHANNEL    = 0

SAMPLE_SIZE = 2048
bSize = int(SAMPLE_SIZE / LED_COUNT)
parsingDistance = int(bSize * 300)

# Initialize LED strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# === NEW: I2C Setup for Two Potentiometers ===
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1
pot3 = AnalogIn(ads, ADS.P3)  # Controls brightness
pot2 = AnalogIn(ads, ADS.P2)     # Controls pattern selection

# === Pattern Definitions ===
def pattern1(avg, chunk):
    returnArray = [[0, 0, 0]] * LED_COUNT
    for i in range(CENTER_LEFT):
        if i < avg:
            returnArray[CENTER_LEFT - i] = [i, 0, CENTER_LEFT - i]
            returnArray[CENTER_RIGHT + i] = [i, 0, CENTER_LEFT - i]
    return returnArray

def pattern2(avg, chunk):
    returnArray = [[0, 0, 0]] * LED_COUNT
    for i in range((CENTER_LEFT)):
         if i < avg:
             returnArray[CENTER_LEFT - i] = [0, CENTER_LEFT - i, i]
             returnArray[CENTER_RIGHT + i] = [0, CENTER_LEFT -i, i]
    return returnArray

# === NEW: Third Pattern Definition ===
def pattern3(avg, chunk):
    rawSpectrum = np.fft.fft(chunk)
    rawSpectrum = np.abs(rawSpectrum)


    scaledSpectrum = [0] * (LED_COUNT)
    returnSpectrum = [[0, 0, 0]] * LED_COUNT
    for i in range(LED_COUNT):
        scaledSpectrum[i] = min((int)(rawSpectrum[i * 4] * 250/4000), 255)

        returnSpectrum[i][2] = scaledSpectrum[i]
    #print(scaledSpectrum)
    return returnSpectrum


# === NEW: List of patterns for modularity ===
patterns = [pattern1, pattern2]  # Add third pattern to the list

# RMS/average calculation
def calculate_avg(data):
    return np.mean(data)

# Audio Input Configuration
p = pyaudio.PyAudio()
RATE = 48000
CHUNK = SAMPLE_SIZE
CHANNELS = 1
FORMAT = pyaudio.paInt16

# Create smoothing window
windowSize = 2
window = [0 for _ in range(windowSize)]

# Show audio devices (debug)
for i in range(p.get_device_count()):
    print(p.get_device_info_by_index(i))

# Open audio stream
stream = p.open(format=FORMAT,
                channels=1,
                rate=RATE,
                input=True,
                input_device_index=1,
                frames_per_buffer=CHUNK)

# Main loop
try:
    while True:
        # === NEW: Read potentiometer inputs ===
        brightness = pot3.voltage / 3.3
        pattern_voltage = pot2.voltage
        pattern_index = int((pattern_voltage / 3.3) * len(patterns))
        pattern_index = max(0, min(pattern_index, len(patterns) - 1))  # Clamp safely

        # Read audio input
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_dat = np.frombuffer(data, dtype=np.int16)

        # Sound level scaling
        scaledLevel = abs(max(audio_dat) - min(audio_dat)) * 300.0 / 1500.0
        scaledLevel -= 10
        scaledLevel = max(0, min(scaledLevel, 299))

        # Smoothing
        avg = 0
        for i in range(windowSize - 1):
            window[i] = window[i + 1]
            avg += window[i]
        window[windowSize - 1] = scaledLevel
        avg += scaledLevel
        avg = int(avg / windowSize)

        # === NEW: Dynamic pattern selection ===
        selected_pattern = patterns[pattern_index]
        finalSelection = selected_pattern(avg, audio_dat)

        # Update LED strip with brightness adjustment
        for i in range(LED_COUNT):
            R = int(finalSelection[i][0] * brightness)
            G = int(finalSelection[i][1] * brightness)
            B = int(finalSelection[i][2] * brightness)
            strip.setPixelColor(i, Color(R, G, B))
        strip.show()

except KeyboardInterrupt:
    print("Exiting...")
    stream.stop_stream()
    stream.close()
    p.terminate()
message.txt
5 KB
