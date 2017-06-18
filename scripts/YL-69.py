import RPi.GPIO as GPIO
import spidev
import time
import mysql.connector as mc

connection = mc.connect(host="localhost",
                        user="mamo",
                        passwd="abc123",
                        db="SENSORENDatabase")

cursor = connection.cursor()

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

def ProcentOm(data):
    result = (100 - data)

    return result

#Kanalen bepalen
moisture_channel = 1
moisture_channel_2 = 2

def main():

    while True:

        # Lees de vocht Sensor Data
        moisture_level = (ReadChannel(moisture_channel) + ReadChannel(moisture_channel_2))/2
        moisture_volts = ConvertVolts(moisture_level, 2)
        moisture_procent = ProcentOm(ConvertProcent(moisture_level))

        q1 = "INSERT INTO tblmetingyl69(MetingYL69, TimeStampMetingYL69,tblYL-69_YL-69ID,tblSysteem_SysteemID) VALUES(moisture_procent,TIMESTAMP(Date, STR_TO_DATE(Time, '%h:%i %p')),1,1)"

        cursor.execute(q1)
        connection.commit()
        time.sleep(1)
        cursor.close()
        connection.close()


def destroy():
    GPIO.cleanup()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        destroy()
