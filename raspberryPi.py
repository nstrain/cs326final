# Lab 4: Program to continuously read A/D converter and log data
import Adafruit_MCP3008
import signal
from datetime import datetime
import RPi.GPIO as GPIO
import subprocess
import requests
# Constants
SAMPLE_TIME = 5
A2D_CHANNEL = 0
LED = 16
IFTTT_LINK = #LEFT OUT
IFTTT_KEY = #LEFT OUT
# SPI pin assignments
CLK = 25
MISO = 24
MOSI = 23
CS = 18
LIGHT = 75
MacNames = #LEFT OUT 
place = 0
#2 mins
LIGHT_MAX = (5)*(60/SAMPLE_TIME)
WEB_LINK = #LEFTOUT 
light_val = [False, 0, LIGHT_MAX]
# Instantiate a new A/D object
a2d = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)
# timer signal callback
def handler(signum, frame):
    try:
        global place
        lostFound = [[],[]]
        print("evaluating")
        current_light = checkLight()
        place = (place + 1) % 12
        if(place%3 == 2):
            lostFound = btCheck()
            uploadStatus(lostFound)
        elif(place == 0):
            syncSQL()
        if(current_light) < LIGHT:
            if(light_val[2] < LIGHT_MAX):
                light_val[2] -= 1
                if light_val[2] == 0:
                    light_val[2] = LIGHT_MAX
                    GPIO.output(LED, False)
                    requests.get(IFTTT_LINK + "pi_off" + IFTTT_KEY)
            if light_val[1] > LIGHT and current_light < LIGHT:
                GPIO.output(LED, True)
                requests.get(IFTTT_LINK + "pi_on" + IFTTT_KEY)
                light_val[2] -= 1
            if (len(lostFound[1]) > 0):
                GPIO.output(LED, True)
                requests.get(IFTTT_LINK + "pi_on" + IFTTT_KEY)
                light_val[2] -= 1


        else:
            GPIO.output(LED, False)
            requests.get(IFTTT_LINK + "pi_off" + IFTTT_KEY)
            light_val[2] = LIGHT_MAX
        light_val[1] = current_light
        print("\tdone")
    except Exception as e:
        print(e)

def checkLight():
    ''' Timer signal handler
    '''
    value = a2d.read_adc(A2D_CHANNEL)
    time = datetime.now().time()

    return value
def btCheck():
    returnList = [[],[]]
    for key in MacNames.keys():
        btName = ""
        btName = str(subprocess.Popen("hcitool name " + str(key),shell=True,stdout=subprocess.PIPE).stdout.read())
        #Not found
        if(not len(btName) > len("b''")):
            #recently lost
            if(MacNames[key][1] > 0):
                returnList[0].append(MacNames[key][0])
                MacNames[key][1] = 0
                continue
        #recently found
        elif(MacNames[key][1] == 0): 
            returnList[1].append(MacNames[key][0])
            MacNames[key][1] = 1
    return returnList



def uploadStatus(lostFound):
    print("\t"+str(lostFound))
    for i in lostFound[0]:
        print("\t\t"+i)
        requests.put(WEB_LINK + i + "/0")
    print("\tFound")
    for i in lostFound[1]:
        print("\t\t"+i)
        requests.put(WEB_LINK + i + "/1")

def syncSQL():
    data = requests.get(WEB_LINK).json()
    for key in MacNames.keys():
        for i in data:
            if(MacNames[key][0] == i['name']):
                if(MacNames[key][1] != i['status']):
                    requests.put(WEB_LINK + i + "/" + str(MackNames[key][1]))
                    continue

# Setup interval timer signal every sample time
signal.signal(signal.SIGALRM, handler)
signal.setitimer(signal.ITIMER_REAL, 1, SAMPLE_TIME)

print('Press Ctrl-C to quit...')
try:
    while True:
        signal.pause()
except KeyboardInterrupt:
    signal.setitimer(signal.ITIMER_REAL, 0, 0) # Cancel inteval timer
    GPIO.cleanup()
    print('Done')

