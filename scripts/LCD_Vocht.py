import RPi.GPIO as GPIO
import spidev
import time
import Adafruit_CharLCD as LCD

# Definieerd de Colommen en lijnen in de LCD
lcd_columns = 16
lcd_rows = 2

DHTPIN = 26

GPIO.setmode(GPIO.BCM)

MAX_UNCHANGE_COUNT = 100

STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5


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

# Delay tussen readings
def read_dht11_dat():
    GPIO.setup(DHTPIN, GPIO.OUT)
    GPIO.output(DHTPIN, GPIO.HIGH)
    time.sleep(0.05)
    GPIO.output(DHTPIN, GPIO.LOW)
    time.sleep(0.02)
    GPIO.setup(DHTPIN, GPIO.IN, GPIO.PUD_UP)

    unchanged_count = 0
    last = -1
    data = []
    while True:
        current = GPIO.input(DHTPIN)
        data.append(current)
        if last != current:
            unchanged_count = 0
            last = current
        else:
            unchanged_count += 1
            if unchanged_count > MAX_UNCHANGE_COUNT:
                break

    state = STATE_INIT_PULL_DOWN

    lengths = []
    current_length = 0

    for current in data:
        current_length += 1

        if state == STATE_INIT_PULL_DOWN:
            if current == GPIO.LOW:
                state = STATE_INIT_PULL_UP
            else:
                continue
        if state == STATE_INIT_PULL_UP:
            if current == GPIO.HIGH:
                state = STATE_DATA_FIRST_PULL_DOWN
            else:
                continue
        if state == STATE_DATA_FIRST_PULL_DOWN:
            if current == GPIO.LOW:
                state = STATE_DATA_PULL_UP
            else:
                continue
        if state == STATE_DATA_PULL_UP:
            if current == GPIO.HIGH:
                current_length = 0
                state = STATE_DATA_PULL_DOWN
            else:
                continue
        if state == STATE_DATA_PULL_DOWN:
            if current == GPIO.LOW:
                lengths.append(current_length)
                state = STATE_DATA_PULL_UP
            else:
                continue
    if len(lengths) != 40:
        return False

    shortest_pull_up = min(lengths)
    longest_pull_up = max(lengths)
    halfway = (longest_pull_up + shortest_pull_up) / 2
    bits = []
    the_bytes = []
    byte = 0

    for length in lengths:
        bit = 0
        if length > halfway:
            bit = 1
        bits.append(bit)
    # print("bits: %s, length: %d" % (bits, len(bits)))
    for i in range(0, len(bits)):
        byte = byte << 1
        if (bits[i]):
            byte = byte | 1
        else:
            byte = byte | 0
        if ((i + 1) % 8 == 0):
            the_bytes.append(byte)
            byte = 0
    # print(the_bytes)
    checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
    if the_bytes[4] != checksum:
        return False

    return the_bytes[0], the_bytes[2]


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
def ProcentOm(data):
    result = (100 - data)
    return result


# Define sensor channels
light_channel = 0
moisture_channel = 1
moisture_channel_2 = 2


def main():
    button_press = 0

    while True:

        result = read_dht11_dat()

        # Lees de Light Sensor Data
        light_level = ReadChannel(light_channel)
        light_volts = ConvertVolts(light_level, 2)
        light_procent = ProcentOm(ConvertProcent(light_level))

        # Lees de vocht Sensor Data
        moisture_level = ReadChannel(moisture_channel)
        moisture_volts = ConvertVolts(moisture_level, 2)
        moisture_procent = ProcentOm(ConvertProcent(moisture_level))

        if (result == False):
            luchtvocht = "Data incorrect"
            temperatuur = "Data incorrect"
        else:
            humidity, temperature = result
            luchtvocht = humidity
            temperatuur = temperature

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
                lcd.message("Temperatuur:                            " + str(temperatuur) + "graden")
            if button_press == 4:
                lcd.clear()
                lcd.message("Luchtvocht:                             " + str(luchtvocht) + "%")
            if button_press == 5:
                lcd.clear()
                button_press = 0

def destroy():
    GPIO.cleanup()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        destroy()
