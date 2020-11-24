"""
Date: August 19, 2020
Purpose: This script collects information from the Arduino that is connected via usb. The information pertains to temperature and humidity values
sent by a DHT11 TemperatureHumidity sensor. This inforation is sent throught the local area network to the raspberry pi, which will post this to
a topic on the google cloud. The messages are viewed by a function scheduled to run a specific time and runs them through a fuzzy controller.
The output will be posted by to the cloud to be viewed by this script and evaluated for an appropriate response displayed by several LEDs and a fan
"""

from google.cloud import pubsub
import pybase64
import socket
import serial
import time

def delay(Time):
    while(time.localtime().tm_sec != Time):
        time.sleep(1)


def line():
    print("--------------------------------------------------------------------------------")
    
    
def callback(message):
    print("Flushing Messages\n")
    message.ack()
    
def acknowledgeMessages():
    subscriber = pubsub.SubscriberClient()
    project = 
    subscription1 = "OutputSubscription1"
    subscription2 = "OutputSubscription2"
    subscription3 = "InputSubscription1"
    subscription4 = "InputSubscription2"
    topic = "OutGoing_Messages"
    subscription_path_1 = subscriber.subscription_path(project, subscription1)
    subscription_path_2 = subscriber.subscription_path(project, subscription2)
    subscription_path_3 = subscriber.subscription_path(project, subscription3)
    subscription_path_4 = subscriber.subscription_path(project, subscription4)
    
    acknowledge = subscriber.subscribe(subscription_path_1,callback) 
    acknowledge = subscriber.subscribe(subscription_path_2,callback) 
    acknowledge = subscriber.subscribe(subscription_path_3,callback)
    acknowledge = subscriber.subscribe(subscription_path_4,callback) 
    
    
def serialRead():
    ser = serial.Serial('/dev/cu.usbmodem14201',9600)                       
    sensorRead = ser.readline()
    sensorRead = sensorRead.decode()                                        
    try:                                                                
        tempValue, humidityValue = sensorRead.split(" ")
    except ValueError:
        tempValue, humidityValue = ser.readline().decode().split(" ")
    except NameError:
       tempValue, humidityValue = ser.readline().decode().split(" ")
    except UnicodeDecodeError:
        tempValue, humidityValue = ser.readline().decode().split(" ")
    ser.close()
    ser.__del__()
    print("Temperature:{} and Humidity:{} values acquired from sensor\n".format(tempValue, humidityValue))
    return tempValue, humidityValue


def Pull(i):
    Foundflag = 0
    subscriber = pubsub.SubscriberClient()
    project = 
    subscription1 = "OutputSubscription1"
    subscription2 = "OutputSubscription2"
    topic = "OutGoing_Messages"
    subscription_path_1 = subscriber.subscription_path(project, subscription1)
    subscription_path_2 = subscriber.subscription_path(project, subscription2)
    pulled_messages_1 = subscriber.pull(subscription_path_1, max_messages = 10)
    pulled_messages_2 = subscriber.pull(subscription_path_2, max_messages = 10)
    for msg in pulled_messages_1.received_messages:
        message = msg.message.data
        decoded_message = pybase64.b64decode(message.decode('utf-8')).decode('utf-8')
        FanPhrase, tagPhrase = decoded_message.split(',')
        tagString, tagValue = tagPhrase.split(":")
        if tagValue == str(i):
            FanString, FanValue = FanPhrase.split(":")
            Foundflag = 1
            return FanValue
    if Foundflag == 0:
        print("Did not find the most recent message in subscription1, trying subscription2")
        for msg in pulled_messages_2.received_messages:
            message = msg.message.data
            decoded_message = pybase64.b64decode(message.decode('utf-8')).decode('utf-8')
            FanPhrase, tagPhrase = decoded_message.split(',')
            tagString, tagValue = tagPhrase.split(":")
            if tagValue == str(i):
                FanString, FanValue = FanPhrase.split(":")
                Foundflag = 1
                return FanValue
        print("Unsuccessful pulling from subscription2, attempting most recent message sent")
        i = i - 1
        FanValue = Pull(i)
        return FanValue


def main():
    ser = serial.Serial('/dev/cu.usbmodem14201', 9600)
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s1.settimeout(300)                                                          
    s1.bind(('0.0.0.0', 1234)) 
    s1.listen(1)  #change back to 1 if noticing issues                                                              
    clientsocket1, address1 = s1.accept()
    #print("Connection from {} and {}]has been established\n".format(address1, address2))
    Temperature = ["1","10","20","30","40","50","60","70","80","90"]
    Humidity = ["99","90","80","70","60","50","40","30","20","10"]
    Temp_Sum = 0
    Hum_Sum = 0
    for i in range(9):
        line()
        print("Iteration {}".format(i+1))
        delay(00)
        if i < 5:
            temperature, humidity = serialRead() #returns as string
            tag = i
            message = "Temperature:{},Humidity:{},tag:{}".format(temperature, humidity, tag)
        else:
            temperature = Temperature[i]
            humidity = Humidity[i]          #these are both strings
            tag = i
            print("Temperature:{} and Humidity:{} values from dummy values".format(temperature, humidity))
            message = "Temperature:{},Humidity:{},tag:{}".format(temperature, humidity, tag)
        byte_message = message.encode('utf-8')
        clientsocket1.send(byte_message) 
        delay(30)
        receivedMessage = Pull(i)              #this is a string
        print("Output message is {}".format(receivedMessage))
        temperature = eval(temperature)
        humidity = eval(humidity)
        FanValue = eval(receivedMessage)
        FanValue = 100*(FanValue)
        Temp_Sum += temperature
        Hum_Sum += humidity
        Avg_Temp = Temp_Sum / (i+1)
        Avg_Hum = Hum_Sum / (i+1)
        print("Average Temp is: {}\nAverage Humidity is: {}".format(Avg_Temp, Avg_Hum))
        if temperature >= (Avg_Temp+5) or temperature <= (Avg_Temp - 5):
            #turn on yellow LED, 4
            Temp_Pin = '4'
            if temperature >= (Avg_Temp + 10) or temperature <= (Avg_Temp - 10):
                #turn on red LED, 5
                Temp_Pin = '5'
        else:
            #turn on green LED, 3
            Temp_Pin = '3'
        if humidity >= (Avg_Hum + 5) or humidity <= (Avg_Hum - 5):
            #turn on yellow LED, 7
            Hum_Pin = '7'
            if humidity >= (Avg_Hum + 10) or humidity <= (Avg_Hum - 10):
                #turn on red LED, 8
                Hum_Pin = '8'
        else:
            #turn on green LED, 6
            Hum_Pin = '6'
        serialString = "{}{}{}".format(Temp_Pin, Hum_Pin, FanValue)
        b_serialString = serialString.encode()
        ser.write(b_serialString)
    s1.close()
    ser.close()
    ser.__del__()
    acknowledgeMessages()
