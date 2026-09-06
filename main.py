import time
from machine import Pin, I2C, ADC
from stemma_soil_sensor import StemmaSoilSensor 

# Setting Pins
# CHECK ALL VALUES
SOIL_SDA_PIN = 4         # I2C SDA for soil sensor 
SOIL_SCL_PIN = 5         # I2C SCL for soil sensor 
PUMP_PIN = 16            # Pump control 
GROW_LIGHT_PIN = 17      # Grow light control
FLOAT_SWITCH_PIN = 10    # Float switch
LDR_ADC_PIN = 28         # Photoresistor ADC pin 


# initialize I2C for the soil sensor
i2c = I2C(0, sda=Pin(SOIL_SDA_PIN), scl=Pin(SOIL_SCL_PIN), freq=400000)
soil_sensor = StemmaSoilSensor(i2c)
seesaw = soil_sensor 

# initialize pump and grow light outputs
pump = Pin(PUMP_PIN, Pin.OUT)
grow_light = Pin(GROW_LIGHT_PIN, Pin.OUT)

# initialize float switch 
float_switch = Pin(FLOAT_SWITCH_PIN, Pin.IN, Pin.PULL_DOWN) 
# initialize photoresistor 
ldr = ADC(LDR_ADC_PIN)

# timing and threshold values
# test mode is for checking
TEST_MODE = True
if TEST_MODE:
    WATERING_INTERVAL = 60  
    MAIN_LOOP_DELAY = 5     
else:
    WATERING_INTERVAL = 300  # seconds between watering cycles
    MAIN_LOOP_DELAY = 10     # seconds between sensor checks

MOISTURE_LOW_THRESHOLD = 600   # soil is considered dry below this value
LIGHT_THRESHOLD = 30000        # supplemental grow light is needed below this value
PUMP_DURATION = 2              # seconds to run the pump, maybe adjust later

# track last watering time
last_watering_time = time.time()



def reinitialize_soil_sensor():
    """
    Reinitializes the I2C connection and the soil sensor.
    Call function if sensor connection fails.
    """
    global i2c, soil_sensor, seesaw
    print("Reinitializing soil sensor...")
    i2c = I2C(0, sda=Pin(SOIL_SDA_PIN), scl=Pin(SOIL_SCL_PIN), freq=400000)
    soil_sensor = StemmaSoilSensor(i2c)
    seesaw = soil_sensor

def read_soil_data():
    """
    Reads soil moisture and temperature.
    Uses a try/except to catch errors during sensor reading
    """
    try:
        moisture = seesaw.get_moisture()
        temperature = seesaw.get_temp()
        return moisture, temperature
    except Exception as e:
        print("Error reading soil sensor:", e)
        time.sleep(10)  # Wait before attempting reinitialization
        reinitialize_soil_sensor()
        return None, None

def control_grow_light(ldr_value):
    """
    Controls growth light based on the light of the environment
    """
    if ldr_value < LIGHT_THRESHOLD:
        grow_light.value(1)
        print("Grow light ON (ambient light low).")
    else:
        grow_light.value(0)
        print("Grow light OFF (ambient light sufficient).")

def check_watering(moisture):
    """
    Checks whether watering is needed and activates the pump if:
      1. The soil moisture is below the threshold value
      2. Enough time has passed since the last watering session
      3. The float switch is not activated and reaches high water level
    """
    global last_watering_time
    current_time = time.time()
    water_level_high = (float_switch.value() == 0)  # 0 indicates high water level
    
    if moisture is None:
        print("Invalid moisture reading; skipping watering cycle.")
        return
    
    if moisture < MOISTURE_LOW_THRESHOLD:
        if current_time - last_watering_time > WATERING_INTERVAL:
            if not water_level_high:
                print("Soil is dry. Activating pump for watering.")
                pump.value(1)
                time.sleep(PUMP_DURATION)
                pump.value(0)
                last_watering_time = current_time  # Update last watering time
            else:
                print("High water level detected. Pump not activated to prevent flooding.")
        else:
            print("Watering happened recently. Waiting for the next interval.")
    else:
        print("Soil moisture is fine. No watering needed.")

def main_loop():
    """
   main loop that:
      - reads sensor data and stores values
      - controls the grow light
      - checks and triggers watering
      
    The loop runs continuously with a delay (MAIN_LOOP_DELAY) between cycles
    """
    while True:
        # read sensors
        moisture, temperature = read_soil_data()
        if moisture is not None and temperature is not None:
            print("Soil Moisture:", moisture, "Temperature: {:.1f}°C".format(temperature))
        else:
            print("Error occurred, no data logged")
        
        ldr_value = ldr.read_u16()
        print("Ambient Light (LDR):", ldr_value)
        
        # call functions
        control_grow_light(ldr_value)
        check_watering(moisture)
        
        # temperature log and warnings
        if temperature is not None:
            if temperature < 10:
                print("Warning: Temperature below optimal range for spinach.")
            elif temperature > 24:
                print("Warning: Temperature above optimal range for spinach.")
        
        # delay before next cycle
        time.sleep(MAIN_LOOP_DELAY)

# start the main function when code is launched
main_loop()
