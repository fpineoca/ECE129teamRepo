import random
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
LAST_INDEX = LED_COUNT - 1
CENTER_LEFT    = 149
CENTER_RIGHT   = 150
LED_PIN        = 12       # GPIO pin connected to the LEDs (GPIO 12, Pin 18)
LED_FREQ_HZ    = 800000   # Frequency of the PWM signal
LED_DMA        = 10       # DMA channel to use for PWM generation
LED_BRIGHTNESS = 200      # Default brightness (0-255)
LED_INVERT     = False    # True to invert the signal
LED_CHANNEL    = 0
SELF_TUNE      = True

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

#lowering this will increase the amount of area covered by the center pulser
centerSize = 5

#increasing this will increase maximum particle speed from the sides
maxParticleSpeed = 7
skipSegLength = 300/maxParticleSpeed
negativeColorLimit = 200

#this controls how fast the particles accelerate towards the center
accelerationConstant = 3
def pattern1(avg, chunk):
    returnArray = [[0, 0, 0]] * LED_COUNT
    #statically recording the previous frame to ONLY parse
    #the list if it's neccissary, so we don't waste computation
    if not hasattr(pattern1, "prevFrame"):
        pattern1.prevFrame = returnArray
    #print(pattern1.prevFrame)
    curLength = (int)(avg/centerSize)

    skipAmount = (int)(avg/skipSegLength) + 2

    #center pulse effect
    for i in range(curLength):
        #300max/10 = a width of 30 for the center pulse effect.
        #feel free to change this constant to control the margines!
        red = 255 #(255*i)/curLength
        green = (255*(curLength - i))/curLength
        blue = 0 #(255*(curLength - i))/curLength
        if avg >= negativeColorLimit:
            red = 0
            green = (curLength - i)*255/curLength
            blue = (i*255)/curLength
        returnArray[CENTER_LEFT - i] = [red, green, blue]
        returnArray[CENTER_RIGHT + i] = [red, green, blue]

    #particle effect
    particleRange = CENTER_LEFT - (curLength+maxParticleSpeed)
    for i in range(1, particleRange):
        diff = i - (skipAmount + (int)(i/accelerationConstant))
        diff2 = (LAST_INDEX - i) + (skipAmount + (int)(i/accelerationConstant))
        if(diff >= 0 and diff <= LAST_INDEX):
            returnArray[i] = pattern1.prevFrame[diff]
            returnArray[LAST_INDEX - i] = pattern1.prevFrame[diff2]
        else:
            returnArray[i] = pattern1.prevFrame[i-1]
            returnArray[LAST_INDEX - i] = pattern1.prevFrame[(LAST_INDEX - i) + 1]
        red = max(0, returnArray[i][0] - 2)
        green = max(0, returnArray[i][1] - i)
        blue = max(0, returnArray[i][2] - i/4)
        returnArray[i] = [red, green, blue]
        returnArray[LAST_INDEX - i] = [(int)(red), (int)(green), (int)(blue)]


        returnArray[0] = [min(avg,255), min(avg,255), min(avg,255)]
        returnArray[LAST_INDEX] = returnArray[0]
    
    pattern1.prevFrame = returnArray
    return returnArray
#this pattern will have particles eminate from the center outwards instead
accelerationRate = 1
soundAccel = 7
def pattern2(avg, chunk):
    returnArray = [[0, 0, 0]] * LED_COUNT
    #statically defining the previous frame to move particles
    if not hasattr(pattern2, "prevFrame"):
        pattern2.prevFrame = returnArray
    returnArray = pattern2.prevFrame

    spawnR = random.randint(1,100) #max(255 - avg, 0)
    spawnG = min(avg,255)
    spawnB = min(avg/4,255)
    
    returnArray[CENTER_LEFT] = [spawnR, spawnG, spawnB]
    returnArray[CENTER_RIGHT] = [spawnR, spawnG, spawnB]
    for i in range(CENTER_LEFT):
        curSound = (int)(avg*soundAccel/255)
        curAccel = (int)(i*accelerationRate/CENTER_LEFT)
        lShiftIndex = max(0, CENTER_LEFT - (i+random.randint(0,6)+curSound + curAccel))
        rShiftIndex = min(299, CENTER_RIGHT + (i+random.randint(0,6)+curSound + curAccel))
        returnArray[lShiftIndex] = pattern2.prevFrame[CENTER_LEFT - i]
        red = max(0, returnArray[lShiftIndex][0] - (2))
        green = max(0, returnArray[lShiftIndex][1] - (3))
        blue = max(0, returnArray[lShiftIndex][2] - (2))
        returnArray[rShiftIndex] = [red, green, blue]
        returnArray[lShiftIndex] = [red, green, blue]
    pattern2.prevFrame = returnArray
    return returnArray

# === NEW: Third Pattern Definition ===
sliderSize = 2
iBinSize = (int)(SAMPLE_SIZE/LED_COUNT)
frontSkip = SAMPLE_SIZE - (LED_COUNT*iBinSize)
def pattern3(avg, chunk):
    rawSpectrum = np.fft.fft(chunk)
    rawSpectrum = np.real(rawSpectrum)

    #scaling the spectrum to a size of 300
    #this represents the new, raw measurment
    scaledSpectrum = [0] * (LED_COUNT)
    
    returnSpectrum = [[0, 0, 0]] * LED_COUNT
    for i in range(LED_COUNT):
        for j in range(iBinSize):
            scaledSpectrum[i] += min((int)(rawSpectrum[i + j + frontSkip] * 250/5000), 255)
        scaledSpectrum[i] = (int)(scaledSpectrum[i]/iBinSize)
    #scaledSpectrum = np.interp(np.linspace(0, 1, LED_COUNT), np.linspace(0, 1, len(rawSpectrum)), rawSpectrum)
    #scaledSpectrum = scaledSpectrum.astype(np.uint16)
    #note that, unlike other patterns, this is tracking a 1d array of magnitudes.
    #Color is added after
    if not hasattr(pattern3, "specWindow"):
        pattern3.specWindow = [[0] * LED_COUNT] * sliderSize
    #avgSpectrum represents the true smoothed average of the frame window
    avgSpectrum = [0] * LED_COUNT
    for i in range(sliderSize - 1):
        pattern3.specWindow[i] = pattern3.specWindow[i + 1]
        for j in range(LED_COUNT):
            avgSpectrum[j] += pattern3.specWindow[i][j]
    for j in range(LED_COUNT):
        pattern3.specWindow[sliderSize - 1][j] = scaledSpectrum[j]
    for j in range(LED_COUNT):
        avgSpectrum[j] += pattern3.specWindow[sliderSize - 1][j]
        avgSpectrum[j] = (int)(avgSpectrum[j]/sliderSize)
    
    #print(avgSpectrum)
    for i in range(LED_COUNT):
       iSkip = (int)((avgSpectrum[i]/16)**2)
       blue = (iSkip*i)/LED_COUNT
       green = (iSkip*(abs(CENTER_RIGHT - i)))/CENTER_RIGHT
       red = (iSkip*(LED_COUNT - i))/LED_COUNT

       returnSpectrum[i] = [red, green, blue]

    return returnSpectrum

def pattern4(avg, chunk):
    returnArray = [[0, 0, 0]] * LED_COUNT
    for i in range(min(LAST_INDEX,avg)):
        red = 0
        blue = min(i, 255)
        green = max(255 - i, 0)
        returnArray[i] = [red, blue, green]
    return returnArray

#this patten uses a few thresholds, tunable below
randomStarThreshold = 0
starSparsity = 20
def pattern5(avg, chunk):
    returnArray = [[0, 0, 0]] * LED_COUNT
    if not hasattr(pattern5, "prevFrame"):
        pattern5.prevFrame = returnArray
    
    for i in range(LED_COUNT):
        if pattern5.prevFrame[i][2] == 0:
            red = max(0, avg - i/10)
        else:
            red = pattern5.prevFrame[i][0] - 8
        green = pattern5.prevFrame[i][1] - 8
        blue = pattern5.prevFrame[i][2] - 8
        returnArray[i] = [ max(0,red), max(0,green), max(0,blue) ]
    if avg > randomStarThreshold:
        for i in range(LED_COUNT):
            if random.randint(1,starSparsity) == 1:
                red = random.randint(1,100)
                green = 0
                blue = min(255,avg)
                returnArray[i] = [red, green, blue]

    pattern5.prevFrame = returnArray
    #print(returnArray)
    return returnArray
# === NEW: List of patterns for modularity ===
patterns = [pattern1, pattern2, pattern4, pattern5, pattern3]  # Add third pattern to the list

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
windowSize = 3
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

#keep track of the amount of local volume and self correct
#this represents the number of times max volume is observed in a row before decreasing sensitivity
upperLimit = 7
uCorrector = 0
#this represents the amount of samples with no max readings needed to increase sensitivity
lowerLimit = 10
lCorrector = 0

#the volume level that the self correcter aims to stay at
volUpperTarget = 220
volLowerTarget = 50

#master scalar to determine sensitivity. Reducing this increases sensitivity
sensitivityScalar = 1200
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
        scaledLevel = abs(max(audio_dat) - min(audio_dat)) * 300 / sensitivityScalar
        scaledLevel = max(0, min(scaledLevel, 299))

        #sensitivity self correction
        if SELF_TUNE == True:
            if scaledLevel >= volUpperTarget:
                uCorrector += 1
            else:
                uCorrector = 0
            if scaledLevel <= volLowerTarget:
                lCorrector += 1
            else:
                lCorrector = 0
            #print(lCorrector, end = ", ")
            #print(uCorrector, end = ", ")
            #print(sensitivityScalar)
            if lCorrector >= lowerLimit:
                sensitivityScalar -= 100
                lCorrector = 0
            if uCorrector >= upperLimit:
                sensitivityScalar += 100
                uCorrector = 0
       
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