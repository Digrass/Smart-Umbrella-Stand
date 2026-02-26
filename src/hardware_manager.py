# hardware_manager.py

import RPi.GPIO as GPIO
import time
import adafruit_dht
import board

# GPIO Pin 설정
FAN_PIN = 17

# 날씨 상태 표시 RGB LED 핀
WEATHER_RGB_RED_PIN = 26
WEATHER_RGB_GREEN_PIN = 19
WEATHER_RGB_BLUE_PIN = 13

# 사용자 우산 위치 표시 LED
USER_UMBRELLA_SPOT1_PIN = 11
USER_UMBRELLA_SPOT2_PIN = 14

# DHT22 습도 센서 핀
DHT_PIN = board.D4

# 초음파 센서 핀
ULTRASONIC_TRIG_PINS = [5, 20, 21]
ULTRASONIC_ECHO_PINS = [6, 23, 24] 

# 센서 객체
dht_sensor = None

# Weather RGB PWM 설정과 상수
weather_rgb_pwm = {}
PWM_FREQUENCY = 100 

ULTRASONIC_SOUND_SPEED = 34300
ULTRASONIC_TIMEOUT = 0.04      

# 하드웨어 초기화 및 정리
def _setup_rgb_led_pins(red_pin, green_pin, blue_pin, pwm_dict):
    """날씨용 RGB LED 설정 (공통 애노드 기준)"""
    GPIO.setup(red_pin, GPIO.OUT)
    GPIO.setup(green_pin, GPIO.OUT)
    GPIO.setup(blue_pin, GPIO.OUT)
   
    pwm_dict['R'] = GPIO.PWM(red_pin, PWM_FREQUENCY)
    pwm_dict['G'] = GPIO.PWM(green_pin, PWM_FREQUENCY)
    pwm_dict['B'] = GPIO.PWM(blue_pin, PWM_FREQUENCY)
   
    for pwm_obj in pwm_dict.values():
        pwm_obj.start(100) # OFF (Common Anode)

def _set_rgb_color(pwm_dict, r, g, b):
    """날씨용 RGB LED 색상 설정"""
    pwm_dict['R'].ChangeDutyCycle(r*100/255)
    pwm_dict['G'].ChangeDutyCycle(g*100/255)
    pwm_dict['B'].ChangeDutyCycle(b*100/255)

def initialize_hardware():
    global dht_sensor, weather_rgb_pwm
   
    print("Initializing hardware...")
    GPIO.setmode(GPIO.BCM)

    # 팬 핀 설정
    GPIO.setup(FAN_PIN, GPIO.OUT)
    GPIO.output(FAN_PIN, GPIO.LOW)

    # 날씨 상태 표시 RGB LED 설정
    _setup_rgb_led_pins(WEATHER_RGB_RED_PIN, WEATHER_RGB_GREEN_PIN, WEATHER_RGB_BLUE_PIN, weather_rgb_pwm)
   
    # 사용자 우산 위치 표시 LED 설정
    GPIO.setup(USER_UMBRELLA_SPOT1_PIN, GPIO.OUT)
    GPIO.setup(USER_UMBRELLA_SPOT2_PIN, GPIO.OUT)
    GPIO.output(USER_UMBRELLA_SPOT1_PIN, GPIO.LOW)
    GPIO.output(USER_UMBRELLA_SPOT2_PIN, GPIO.LOW)

    # 초음파 센서 핀 설정
    for trig_pin, echo_pin in zip(ULTRASONIC_TRIG_PINS, ULTRASONIC_ECHO_PINS):
        GPIO.setup(trig_pin, GPIO.OUT)
        GPIO.setup(echo_pin, GPIO.IN)
        GPIO.output(trig_pin, GPIO.LOW)
   
    # DHT22 센서 객체 생성
    try:
        dht_sensor = adafruit_dht.DHT22(DHT_PIN)
    except Exception as e:
        print(f"Error initializing DHT sensor: {e}.")
        dht_sensor = None

    reset_leds() 
    time.sleep(1)
    print("Hardware initialization complete.")

def cleanup_hardware():
    print("Cleaning up hardware...")
    if dht_sensor:
        dht_sensor.exit()
   
    # Weather PWM 정지
    for pwm_obj in weather_rgb_pwm.values():
        pwm_obj.stop()

    GPIO.cleanup()
    print("Hardware cleanup complete.")

#초음파 센서 제어
def _measure_distance(trig_pin, echo_pin):
    GPIO.output(trig_pin, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(trig_pin, GPIO.LOW)

    pulse_start_time = time.time()
    pulse_end_time = time.time()

    timeout_start = time.time()
    while GPIO.input(echo_pin) == GPIO.LOW:
        if time.time() - timeout_start > ULTRASONIC_TIMEOUT:
            return -1
        pulse_start_time = time.time()

    timeout_start = time.time()
    while GPIO.input(echo_pin) == GPIO.HIGH:
        if time.time() - timeout_start > ULTRASONIC_TIMEOUT:
            return -1
        pulse_end_time = time.time()

    pulse_duration = pulse_end_time - pulse_start_time
    distance = (pulse_duration * ULTRASONIC_SOUND_SPEED) / 2
    return round(distance, 2)

def detect_person_ultrasonic(threshold_cm=10):
    """입구쪽 초음파 센서(인덱스 0)로 사람 감지"""
    distance = _measure_distance(ULTRASONIC_TRIG_PINS[0], ULTRASONIC_ECHO_PINS[0])
    #print(distance)
    return 0 < distance <= threshold_cm

# 습도 센서 제어
def get_humidity():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            humidity = dht_sensor.humidity
            if humidity is not None and 0 <= humidity <= 100:
                return humidity
            print(f"Failed to read humidity (Attempt {attempt + 1}/{max_retries})...")
        except Exception as e:
            print(f"DHT22 Sensor Error: {e}")
        time.sleep(2.0) 
    return None

# 팬 제어
def turn_on_fan():
    GPIO.output(FAN_PIN, GPIO.HIGH)
    print("Fan ON")

def turn_off_fan():
    GPIO.output(FAN_PIN, GPIO.LOW)
    print("Fan OFF")

# LED 제어
def set_weather_led_color(rain_level):
    """0:초록, 1:파랑, 2:노랑, 3:빨강"""
    colors = {
        0: (0, 255, 0),   # Green
        1: (0, 0, 255),   # Blue
        2: (255, 255, 0), # Yellow
        3: (255, 0, 0)    # Red
    }
    r, g, b = colors.get(rain_level, (0, 0, 0))
    _set_rgb_color(weather_rgb_pwm, r, g, b)
    print(f"Weather LED Rain Level {rain_level}")

def highlight_user_umbrella_spot(user_id, spot_id, turn_on=True):
    state = GPIO.HIGH if turn_on else GPIO.LOW
    
    if spot_id == 1:
        GPIO.output(USER_UMBRELLA_SPOT1_PIN, state)
        print(f"Spot 1 LED {'ON' if turn_on else 'OFF'} for user {user_id}")
    elif spot_id == 2:
        GPIO.output(USER_UMBRELLA_SPOT2_PIN, state)
        print(f"Spot 2 LED {'ON' if turn_on else 'OFF'} for user {user_id}")

def reset_leds():
    _set_rgb_color(weather_rgb_pwm, 0, 0, 0)
    GPIO.output(USER_UMBRELLA_SPOT1_PIN, GPIO.LOW)
    GPIO.output(USER_UMBRELLA_SPOT2_PIN, GPIO.LOW)
    print("All LEDs (Weather & Spots) reset to OFF.")

# 특정 자리의 우산 유무 확인
def get_spot_umbrella_status(spot_id, prev_status):
    if not (1 <= spot_id <= 2):
        return False

    trig_pin = ULTRASONIC_TRIG_PINS[spot_id]
    echo_pin = ULTRASONIC_ECHO_PINS[spot_id]
    threshold = 8 if prev_status else 5
    detected = 0;
    for i in range (8):
        distance = _measure_distance(trig_pin, echo_pin)
        time.sleep(0.2) 
        if distance < 0:
            #print(spot_id, distance)
            continue
        if (distance <threshold):
            detected += 1
            #print(spot_id, distance)
    
    # 히스테리시스 적용
    if (5 <detected):
        return True
    else:
        return False
