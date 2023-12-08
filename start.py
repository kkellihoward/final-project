import os
import time
import sys
from time import sleep
import RPi.GPIO as GPIO
from PCA9685 import PCA9685
from tempfile import NamedTemporaryFile
import pyttsx3

detection_file_path = "output.txt"


# AUDIO OUTPUT
def text_to_speech(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 100)  # Adjust the rate (words per minute)        
    engine.say(text)
    engine.runAndWait()
    return
    


# DETECTION
def is_object_detected():
    print("Finding object")
    # Initialize the variable to store the last line
    last_line = None

    # Open the file in read mode
    with open(detection_file_path, "r") as file:
        # Read all lines from the file
        lines = file.readlines()

        # Check if there are any lines in the file
        if lines:
            # Save the last line to the variable
            last_line = lines[-1].strip()

    # Check if the file is empty
    if (os.path.getsize(detection_file_path) == 0 or len(last_line) == 0):
        return False
    else:
        destroy()
        print("Object detected at:")
        print(len(last_line))
        return True
    
def read_detection_file():
    # Initialize the variable to store the last line
    last_line = None

    # Open the file in read mode
    with open(detection_file_path, "r") as file:
        # Read all lines from the file
        lines = file.readlines()

        # Check if there are any lines in the file
        if lines:
            # Save the last line to the variable
            last_line = lines[-1].strip()

    # Print or use the last line
    if last_line is not None:
        print(f"The last line in the file is: \n{last_line}")
    else:
        print("The file is empty.")

def object_position():
    # Initialize the variable to store the last line
    last_line = None

    # Open the file in read mode
    with open(detection_file_path, "r") as file:
        # Read all lines from the file
        lines = file.readlines()

        # Check if there are any lines in the file
        if lines:
            # Save the last line to the variable
            last_line = lines[-1].strip()
    
    # Find the index of the first comma
    comma_index = last_line.find(',')
    x_pos = last_line if comma_index == -1 else last_line[:comma_index]

    # Remove the last ',' if present
    x_pos = x_pos.rstrip(',')
    x_pos = int(x_pos[3:])

    return x_pos



# ULTRASONIC
class Ultrasonic:
    def __init__(self):
        GPIO.setwarnings(False)
        self.trigger_pin = 27
        self.echo_pin = 22
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin,GPIO.OUT)
        GPIO.setup(self.echo_pin,GPIO.IN)
    def send_trigger_pulse(self):
        GPIO.output(self.trigger_pin,True)
        time.sleep(0.00015)
        GPIO.output(self.trigger_pin,False)

    def wait_for_echo(self,value,timeout):
        count = timeout
        while GPIO.input(self.echo_pin) != value and count>0:
            count = count-1
     
    def get_distance(self):
        distance_cm=[0,0,0,0,0]
        for i in range(3):
            self.send_trigger_pulse()
            self.wait_for_echo(True,10000)
            start = time.time()
            self.wait_for_echo(False,10000)
            finish = time.time()
            pulse_len = finish-start
            distance_cm[i] = pulse_len/0.000058
        distance_cm=sorted(distance_cm)
        print(distance_cm[2])
        return int(distance_cm[2])

ultrasonic = Ultrasonic()



# MOVEMENT CODE
# Set up the motor class which moves the rover
class Motor:
    def __init__(self):
        self.pwm = PCA9685(0x40, debug=True)
        self.pwm.setPWMFreq(50)
    def duty_range(self,duty1,duty2,duty3,duty4):
        if duty1>4095:
            duty1=4095
        elif duty1<-4095:
            duty1=-4095        
        
        if duty2>4095:
            duty2=4095
        elif duty2<-4095:
            duty2=-4095
            
        if duty3>4095:
            duty3=4095
        elif duty3<-4095:
            duty3=-4095
            
        if duty4>4095:
            duty4=4095
        elif duty4<-4095:
            duty4=-4095
        return duty1,duty2,duty3,duty4
        
    def left_Upper_Wheel(self,duty):
        if duty>0:
            self.pwm.setMotorPwm(0,0)
            self.pwm.setMotorPwm(1,duty)
        elif duty<0:
            self.pwm.setMotorPwm(1,0)
            self.pwm.setMotorPwm(0,abs(duty))
        else:
            self.pwm.setMotorPwm(0,4095)
            self.pwm.setMotorPwm(1,4095)
    def left_Lower_Wheel(self,duty):
        if duty>0:
            self.pwm.setMotorPwm(3,0)
            self.pwm.setMotorPwm(2,duty)
        elif duty<0:
            self.pwm.setMotorPwm(2,0)
            self.pwm.setMotorPwm(3,abs(duty))
        else:
            self.pwm.setMotorPwm(2,4095)
            self.pwm.setMotorPwm(3,4095)
    def right_Upper_Wheel(self,duty):
        if duty>0:
            self.pwm.setMotorPwm(6,0)
            self.pwm.setMotorPwm(7,duty)
        elif duty<0:
            self.pwm.setMotorPwm(7,0)
            self.pwm.setMotorPwm(6,abs(duty))
        else:
            self.pwm.setMotorPwm(6,4095)
            self.pwm.setMotorPwm(7,4095)
    def right_Lower_Wheel(self,duty):
        if duty>0:
            self.pwm.setMotorPwm(4,0)
            self.pwm.setMotorPwm(5,duty)
        elif duty<0:
            self.pwm.setMotorPwm(5,0)
            self.pwm.setMotorPwm(4,abs(duty))
        else:
            self.pwm.setMotorPwm(4,4095)
            self.pwm.setMotorPwm(5,4095)
            
 
    def setMotorModel(self,duty1,duty2,duty3,duty4):
        duty1,duty2,duty3,duty4=self.duty_range(duty1,duty2,duty3,duty4)
        self.left_Upper_Wheel(duty1)
        self.left_Lower_Wheel(duty2)
        self.right_Upper_Wheel(duty3)
        self.right_Lower_Wheel(duty4)

PWM = Motor() 
            
def search():
    object_not_found = True
    time_ = 0.25
    
    while(object_not_found & (time_ < 2)):
        # Before moving, check to see if we found the object
        if(is_object_detected()):
            object_not_found = False
            break
        # Move forward
        PWM.setMotorModel(-2000, -2000, -2000, -2000)
        time.sleep(time_)
        destroy()
        time.sleep(3.5)
        # Move left
        PWM.setMotorModel( 2000,2000,-500,-500)
        time.sleep(0.9)
        destroy()
        time.sleep(3.5)

        # Before moving, check to see if we found the object
        if(is_object_detected()):
            object_not_found = False
            break
        # Move Forward
        PWM.setMotorModel( -2000, -2000, -2000, -2000)
        time.sleep(time_)
        destroy()
        time.sleep(4)
        # Move Left
        PWM.setMotorModel( 2000,2000,-500,-500)
        time.sleep(0.9)
        destroy()
        time.sleep(3.5)

        # Before moving, check to see if we found the object
        if(is_object_detected()):
            object_not_found = False
            break
        # Move forward
        PWM.setMotorModel( -2000, -2000, -2000, -2000)
        time.sleep(time_)
        destroy()
        time.sleep(3.5)
        # Move left
        PWM.setMotorModel( 2000,2000,-500,-500)
        time.sleep(0.9)
        destroy()
        time.sleep(3.5)

        # Before moving, check to see if we found the object
        if(is_object_detected()):
            object_not_found = False
            break
        # Move Forward
        PWM.setMotorModel( -2000, -2000, -2000, -2000)
        time.sleep(time_)
        destroy()
        time.sleep(3.5)
        # Move Left
        PWM.setMotorModel( 2000,2000,-500,-500)
        time.sleep(0.9)
        destroy()
        time.sleep(3.5)

        time_ = time_ + 0.5

    destroy()  

def go_to_object():
    print("Now we will move to the object")
    print(object_position())
    while(ultrasonic.get_distance() > 14):
        if(object_position() < 150):
            while(object_position() < 150):
                # Move right
                print("Need to turn right")
                print(ultrasonic.get_distance())
                if(ultrasonic.get_distance() < 20):
                    break;
                PWM.setMotorModel(-500,-500,2000,2000)
                time.sleep(0.15)
                destroy()
                time.sleep(4)
        if(object_position() > 350):
            while(object_position() > 350):
                # Move left
                print("Need to turn left")
                print(ultrasonic.get_distance())
                if(ultrasonic.get_distance() < 20):
                    break;
                PWM.setMotorModel(2000,2000,-500,-500)
                time.sleep(0.15)
                destroy()
                time.sleep(4)
        else:
			# Move forward
            print(ultrasonic.get_distance())
            if(ultrasonic.get_distance() < 20):
                break;
            PWM.setMotorModel(-2000, -2000, -2000, -2000)
            time.sleep(0.9)
            destroy()
            time.sleep(4)
			
    print("The object is now in front of us")
    
    while(ultrasonic.get_distance() > 9):
        # Move forward
        PWM.setMotorModel(-2000, -2000, -2000, -2000)
        time.sleep(0.15)
        destroy()
        time.sleep(3.5)
        

    item = sys.argv[1]
    text_to_speech(f"the {item} object has been located")   
    print("We found the object!")


def destroy():
    PWM.setMotorModel(0,0,0,0)  

def start():
    search()
    if(is_object_detected() == False):
        print("Failed to find the object")
    go_to_object()



# Start of program
if __name__ == '__main__':
    try:
        start()

    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        destroy()
