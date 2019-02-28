from RPiSim.GPIO import GPIO


GPIO.setmode(GPIO.BCM)

GPIO.setup(3,GPIO.IN,initial=GPIO.HIGH,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(5,GPIO.IN,initial=GPIO.LOW,pull_up_down=GPIO.PUD_DOWN)



