import RPi.GPIO as GPIO
import spidev
import time
import Adafruit_CharLCD as LCD

# Definieerd de Colommen en lijnen in de LCD
lcd_columns = 16
lcd_rows = 2

# Declaratie pinnen LCD
lcd_rs = 25
lcd_en = 24
lcd_d4 = 23
lcd_d5 = 17
lcd_d6 = 18
lcd_d7 = 22
lcd_backlight = 2

lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

GPIO.setmode(GPIO.BCM)

# Declaratie Button
button = 5

GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)


# Functie om de SPI data te lezen van de MCP3008 chip
# De channeld moet een integer 0-7
def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


# Functie om data te converteren naar voltage
def ConvertVolts(data, places):
    volts = (data * 3.3) / float(1023)
    volts = round(volts, places)
    return volts


# Functie om uw waarde om te zetten in procent
def ConvertProcent(data):
    procent = (data * 100) / float(1023)

    # Om het procent af te ronden op 2 cijfers na de komma
    return round(procent, 2)


# Functie om de temperetuur te bereken
def ConvertTemp(data, places):
    temp = ((data * 330) / float(1023)) - 50
    temp = round(temp, places)
    return temp

#Functie om waarde om te wisselen
def WisselLicht(data):
    result = 100 - data
    return result


# Define sensor channels
light_channel = 0
moisture_channel = 1
moisture_channel_2 = 2


def main():
    button_press = 0

    while True:

        # Lees de Light Sensor Data
        light_level = ReadChannel(light_channel)
        light_volts = ConvertVolts(light_level, 2)
        light_procent = WisselLicht(ConvertProcent(light_level))

        # Lees de vocht Sensor Data
        moisture_level = ReadChannel(moisture_channel)
        moisture_volts = ConvertVolts(moisture_level, 2)
        moisture_procent = ConvertProcent(moisture_level)

        lcd.set_backlight(0)

        # Button code
        input_state = GPIO.input(5)
        if input_state == False:
            button_press += 1
            time.sleep(0.2)

            if button_press == 1:
                lcd.clear()
                lcd.message("Licht:                                  " + str(light_procent) + "%")
            if button_press == 2:
                lcd.clear()
                lcd.message("Bodemvocht:                             " + str(moisture_procent) + "%")
            if button_press == 3:
                lcd.clear()
                button_press = 0


def destroy():
    GPIO.cleanup()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        destroy()
