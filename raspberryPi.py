# project for cs 326
# written by Nathan Strain and Sam Mayfield
import Adafruit_MCP3008
import signal
from datetime import datetime
import RPi.GPIO as GPIO
import subprocess
import requests
import sys
#imports personal info which needs to be created individually
from personalInfo import *

# Constants
SAMPLE_TIME = 5 #seconds
A2D_CHANNEL = 0
LED = 16
MIN_LIGHT = 75 # minimum light value to turn on
MAX_LIGHT = 90 # value to turn light off at
LIGHT_SHUTOFF_TIME = (5)*(60/SAMPLE_TIME)   #5 min

# SPI pin assignments
CLK = 25
MISO = 24
MOSI = 23
CS = 18

#this is a constant determined by command line arugment
SQL_SYNC = False
if __name__ == "__main__":
    #if command line argument -sql-sync is passed, enable sql syncing
    if("-sql-sync" in sys.argv):
        SQL_SYNC = True
        print("WARNING: You are sharing your room presence with the world")



#other intialization

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
        global timeOn
        global previousLightValue
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
        
        if currentLight < MAX_LIGHT:
            #if the light timer timeOn is not full keep decrementing it
            if timeOn < LIGHT_SHUTOFF_TIME:
                timeOn -= 1
                #if the timer runs out turn the light off and reset timer to 5 min
                if timeOn <= 0:
                    timeOn = LIGHT_SHUTOFF_TIME
                    turnLight(False)
            #if the last light value was above the threshold and the current light 
            #value is below it turn the light on and start the timer
            elif previousLightValue >= MIN_LIGHT and currentLight < MIN_LIGHT:
                turnLight(True)
                timeOn -= 1
            #if there have been any new devices found turn on the light and reset the timer
            if (len(lostFoundDevices["found"]) > 0):
                turnLight(True)
                timeOn = LIGHT_SHUTOFF_TIME - 1
        #if the current light is >= MAX_LIGHT and the led is on turn it off and reset the timer
        elif currentLight >= MAX_LIGHT and GPIO.input(LED):
            turnLight(False)
            timeOn = LIGHT_SHUTOFF_TIME
        previousLightValue = currentLight
        print("\tdone")
    except Exception as e:
        print(e)
        print(sys.exec_info())

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
            if(MacNames[macAddress]["status"] == 1):
                lostFoundDevices["lost"].append(MacNames[macAddress]["name"])
                MacNames[macAddress]["status"] = 0
                continue
        #else there must have been a response so update the presence to True if it was False
        elif(MacNames[macAddress]["status"] == 0): 
            lostFoundDevices["found"].append(MacNames[macAddress]["name"])
            MacNames[macAddress]["status"] = 1
    return lostFoundDevices


# function to upload the presence of devices to the sql server
def uploadStatus(lostFound):
    # only run if sql-syncing has been enabled
    if SQL_SYNC:
        print("\t"+str(lostFound))
        for device in lostFound["lost"]:
            print("\t\t" + str(device))
            #print ("\t" + WEB_LINK + str(device) + "/0")
            requests.put(WEB_LINK + str(device) + "/0") #update sql database to say device is present
        print("\tFound")
        for device in lostFound["found"]:
            print("\t\t" + str(device))
            requests.put(WEB_LINK + str(device) + "/1") #update sql database to say device is not present

#function that makes sure all of the data in the sql server is updated
def syncSQL():
    # only run if sql-syncing has been enabled
    if SQL_SYNC:
        data = requests.get(WEB_LINK).json()  # retrieves sql data
        # checks that all of the data in the sql server is updated
        for macAddress in MacNames.keys():
            for i in data:
                if(MacNames[macAddress]["name"] == i['name']):
                    if(MacNames[macAddress]["status"] != i['status']):
                        requests.put(WEB_LINK + i['name'] + "/" + str(MacNames[macAddress]["status"]))
                        print(WEB_LINK + i['name'] + "/" + str(MacNames[macAddress]["status"]))
                        continue
        
# Setup interval timer signal every sample time
signal.signal(signal.SIGALRM, handler)
signal.setitimer(signal.ITIMER_REAL, 1, SAMPLE_TIME)



print('Press Ctrl-C to quit...')
try:
    while True:
        #pauses the process until a signal is received
        signal.pause()
except KeyboardInterrupt:
    signal.setitimer(signal.ITIMER_REAL, 0, 0) # Cancel inteval timer
    GPIO.cleanup()
    print('Done')

