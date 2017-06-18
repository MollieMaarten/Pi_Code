import RPi.GPIO as GPIO
import spidev
import time

DHTPIN = 26

GPIO.setmode(GPIO.BCM)

MAX_UNCHANGE_COUNT = 100

STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5

# Declaratie Button
button = 5

delay = 5

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


# Define sensor channels
light_channel = 0
moisture_channel = 1
moisture_channel_2 = 2


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
        print("Data DHT11 not good, skip")
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
        print("Data DHT11 not good, skip")
        return False

    return the_bytes[0], the_bytes[2]


def main():
    print("Slimme Serre")

    while True:

        result = read_dht11_dat()

        # Lees de Light Sensor Data
        light_level = ReadChannel(light_channel)
        light_volts = ConvertVolts(light_level, 2)
        light_procent = ConvertProcent(light_level)

        # Lees de vocht Sensor Data
        moisture_level = ReadChannel(moisture_channel)
        moisture_volts = ConvertVolts(moisture_level, 2)
        moisture_procent = ConvertProcent(moisture_level)

        # Print de resultaten
        print("--------------------------------------")
        print("WAARDEN SENSOREN")
        print("Licht: {0} [{1}%] ({2}V)".format(light_level, light_procent, light_volts))
        print("Bodem_Vocht: {0} [{1}%] ({2}V)".format(moisture_level, moisture_procent, moisture_volts))

        if result:
            humidity, temperature = result

            print("Lucht_vochtigheid: %s %%,\nTemperatuur: %s C`" % (humidity, temperature))
        print("--------------------------------------")
        time.sleep(delay)


def destroy():
    GPIO.cleanup()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        destroy()
