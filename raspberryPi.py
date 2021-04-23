# project for cs 326
# written by Nathan Strain and Sam Mayfield
import Adafruit_MCP3008
import signal
from datetime import datetime
import RPi.GPIO as GPIO
import subprocess
import requests

# Constants
SAMPLE_TIME = 5 #seconds
A2D_CHANNEL = 0
LED = 16
MIN_LIGHT = 75 # minimum light value to turn on
LIGHT_SHUTOFF_TIME = (5)*(60/SAMPLE_TIME)   #5 min
WEB_LINK = #LEFTOUT 
IFTTT_LINK = #LEFT OUT
IFTTT_KEY = #LEFT OUT

# SPI pin assignments
CLK = 25
MISO = 24
MOSI = 23
CS = 18

#other intialization

MacNames = {"MACADDRESS": {"name": "george",  "present": False}} #george is the name to be displayed on the web page, 
#and 0 is the presence of the device: 0 not present, 1 present
place = 0
light_val = [False, 0, LIGHT_SHUTOFF_TIME]
previousLightValue = 0
timeOn = LIGHT_SHUTOFF_TIME

# Instantiate a new A/D object
a2d = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
#setup led
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)

# timer signal callback
def handler(signum, frame):
    try:
        global place
        lostFoundDevices = {
            "found": [],
            "lost": []
        }
        print("evaluating")
        currentLight = checkLight()

        #run these functions intermittently staggered so taht btcheck 
        #and upload status don't run at the same time as syncsql
        place = (place + 1) % 12
        if(place%3 == 2):
            lostFoundDevices = btCheck()
            uploadStatus(lostFoundDevices)
        elif(place == 0):
            syncSQL()
        
        if currentLight < MIN_LIGHT:
            #if the light timer timeOn is not full keep decrementing it
            if(timeOn < LIGHT_SHUTOFF_TIME):
                timeOn -= 1
                #if the timer runs out turn the light off and reset timer to 5 min
                if timeOn == 0:
                    timeOn = LIGHT_SHUTOFF_TIME
                    turnLight(False)
            #if the light value was above the threshold turn the light on and start the timer
            if previousLightValue > MIN_LIGHT:
                turnLight(True)
                timeOn -= 1
            #if there have been any new devices found turn on the light and restart the timer
            if (len(lostFoundDevices["found"]) > 0):
                turnLight(True)
                timeOn = LIGHT_SHUTOFF_TIME - 1
        #if the light value is greater than MIN_Light
        else:
            turnLight(False)
            timeOn = LIGHT_SHUTOFF_TIME
        previousLightValue = currentLight
        print("\tdone")
    except Exception as e:
        print(e)

#function to check the light values
def checkLight():
    ''' Timer signal handler
    '''
    value = a2d.read_adc(A2D_CHANNEL)
    #time = datetime.now().time()

    return value

#function to turn the led on/off and the smart outlet on/off
def turnLight(onOff):
    if onOff == True:
        GPIO.output(LED, True)
        requests.get(IFTTT_LINK + "pi_on" + IFTTT_KEY)
    if onOff == False:
        GPIO.output(LED, False)
        requests.get(IFTTT_LINK + "pi_off" + IFTTT_KEY)
    
#function to check for the bluetooth devices specified in MacNames
def btCheck():
    lostFoundDevices = {
        "found": [],
        "lost": []
    }

    for macAddress in MacNames.keys():
        btName = ""
        #ping mac address asking for the name of the device, which will be stored in btName
        btName = str(subprocess.Popen("hcitool name " + str(macAddress),shell=True,stdout=subprocess.PIPE).stdout.read())
        #if the name returned is really short therefore the device is no longer in range
        if( len(btName) <= len("b''")):
            #if the phone just recently disappeared 
            if(MacNames[macAddress]["present"] == True):
                lostFoundDevices["lost"].append(MacNames[macAddress]["name"])
                MacNames[macAddress]["present"] = False
                continue
        #else there must have been a response so update the presence to true if it was False
        elif(MacNames[macAddress]["present"] == False): 
            lostFoundDevices["found"].append(MacNames[macAddress]["name"])
            MacNames[macAddress]["present"] = True
    return lostFoundDevices


# function to upload the presence of devices to the sql server
def uploadStatus(lostFound):
    print("\t"+str(lostFound))
    for device in lostFound["lost"]:
        print("\t\t" + device)
        requests.put(WEB_LINK + device + "/0") #update sql database to say device is present
    print("\tFound")
    for device in lostFound["found"]:
        print("\t\t" + device)
        requests.put(WEB_LINK + device + "/1") #update sql database to say device is not present

def syncSQL():
    data = requests.get(WEB_LINK).json()
    for macAddress in MacNames.keys():
        for i in data:
            if(MacNames[macAddress]["name"] == i['name']):
                if(MacNames[macAddress]["present"] != i['status']):
                    requests.put(WEB_LINK + i + "/" + str(MacNames[macAddress]["present"]))
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

