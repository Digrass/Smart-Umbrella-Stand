import time
from faceRec import start_camera, run_inference, stop_camera, show_black_screen
from pop import getPop

import hardware_manager
import umbrella_storage

# 우산 보관함 초기화
umbrella_box = umbrella_storage.UmbrellaStorage()

# 시스템 상태 정의
STATE_IDLE = "IDLE"
STATE_PERSON_DETECTED = "PERSON_DETECTED"
STATE_USER_RECOGNIZED = "USER_RECOGNIZED"
STATE_UMBRELLA_ACTIVITY = "UMBRELLA_ACTIVITY"

current_system_state = STATE_IDLE
last_detected_user = None 
last_weather_rain_level = 0 

window_name = "rec"

# 사용자-자리 매핑
USER_SPOT_MAPPING = {
    "user_A": 1,
    "user_B": 2
}
SPOT_USER_MAPPING = {
    1: "user_A",
    2: "user_B"
}

NO_PERSON_THRESHOLD = 2  
no_person_count = 0      

def turn_off_all_user_spots():
    """모든 사용자 우산 자리 LED를 끕니다."""
    hardware_manager.highlight_user_umbrella_spot(None, 1, turn_on=False)
    hardware_manager.highlight_user_umbrella_spot(None, 2, turn_on=False)

def main_loop():
    global current_system_state, last_detected_user, last_weather_rain_level

    hardware_manager.initialize_hardware() # 하드웨어 초기화
    hardware_manager.reset_leds() # 모든 LED 초기 상태로
    p, det, rec, id2name = start_camera()
    print("Camera initialized")
    print("시스템 시작. IDLE 상태.")
    show_black_screen(window_name)

    try:
        while True:
            # 1. 사람 감지 (초음파 센서)
            #print("loop entered")
            if hardware_manager.detect_person_ultrasonic(threshold_cm=10):
                no_person_count = 0 
                if current_system_state == STATE_IDLE:
                    current_system_state = STATE_PERSON_DETECTED
                    print("사람 감지됨. 사용자 인식 시도.")
                    
                    # 날씨 정보 가져와서 LED 설정
                    try:
                        # 실제 API 호출
                        last_weather_rain_level = getPop(lat=37.26, lon=127.05)
                        # 테스트용 (필요시 주석 해제)
                        # last_weather_rain_level = 1 
                    except Exception as e:
                        print(f"날씨 정보 가져오기 실패: {e}")
                        last_weather_rain_level = 0
                        
                    hardware_manager.set_weather_led_color(last_weather_rain_level)
                    
                # 2. 사용자 인식 (사람 감지 상태에서만)
                if current_system_state == STATE_PERSON_DETECTED:
                    user_id = run_inference(p, det, rec, id2name, timeout=30)
                    show_black_screen(window_name)
                    print("Detected User:", user_id)
                    
                    if user_id:
                        if user_id not in USER_SPOT_MAPPING: # 등록되지 않은 사용자
                            print(f"미등록 사용자 감지. 무시합니다.")
                            turn_off_all_user_spots()
                            current_system_state = STATE_IDLE
                            time.sleep(2) 
                            continue

                        last_detected_user = user_id
                        current_system_state = STATE_USER_RECOGNIZED
                        print(f"사용자 '{user_id}' 인식됨.")
                        
                        # 인식된 사용자의 고정된 우산 위치 LED 점등 (True 전달)
                        user_assigned_spot = umbrella_box.get_user_umbrella_spot(user_id)
                        
                        if user_assigned_spot is not None:
                            hardware_manager.highlight_user_umbrella_spot(user_id, user_assigned_spot, turn_on=True)
                            print(f"사용자 '{user_id}'의 우산 위치 점등: 자리 {user_assigned_spot}")
                        else:
                            print(f"경고: 사용자 '{user_id}'에 할당된 고정 자리가 없습니다.")
                            turn_off_all_user_spots()

                    else:
                        print("사용자 인식 실패. IDLE 상태로 복귀.")
                        turn_off_all_user_spots()
                        current_system_state = STATE_IDLE 
                        time.sleep(1) 
                        continue

            else: # 사람이 감지되지 않음
                if current_system_state != STATE_IDLE:
                    no_person_count += 1
                    if no_person_count >= NO_PERSON_THRESHOLD:
                        print("사람이 사라짐. 시스템 리셋.")
                        hardware_manager.reset_leds()
                        last_detected_user = None
                        current_system_state = STATE_IDLE
                        no_person_count = 0 
                
            # 3. 우산 유무 확인 및 처리 (항상 확인)
            for spot_id in range(1, umbrella_box.num_spots + 1): 
                new_umbrella_status = hardware_manager.get_spot_umbrella_status(spot_id, umbrella_box.get_spot_status(spot_id))

                # 우산 상태 변화 감지
                if umbrella_box.get_spot_status(spot_id) != new_umbrella_status:
                    if(current_system_state == STATE_IDLE):
                        current_system_state = STATE_UMBRELLA_ACTIVITY
                    
                    if new_umbrella_status: # 우산이 새로 생김 (반납)
                        print(f"자리 {spot_id}에 우산이 새로 들어옴.")
                        
                        assigned_user_for_spot = SPOT_USER_MAPPING.get(spot_id)
                        if assigned_user_for_spot:
                            umbrella_box.update_spot_status(spot_id, True, assigned_user_for_spot)
                            print(f"-> 자리 {spot_id}는 사용자 '{assigned_user_for_spot}'의 우산으로 할당.")
                        else:
                            print(f"경고: 자리 {spot_id}에 할당된 사용자가 없습니다.")

                        # 습도 확인 후 팬 작동
                        current_humidity = hardware_manager.get_humidity()
                        if current_humidity is not None and current_humidity > 20: 
                            print(f"습도 {current_humidity:.1f}% 감지. 팬 작동.")
                            hardware_manager.turn_on_fan()
                            time.sleep(10) 
                            hardware_manager.turn_off_fan()
                            print("팬 작동 종료.")
                        else:
                            print(f"습도 {current_humidity:.1f}%. 팬 작동 안 함.")
                        
                        last_detected_user = None
                        no_person_count = 0
                        if(current_system_state == STATE_UMBRELLA_ACTIVITY):
                            current_system_state = STATE_IDLE 

                    else: # 우산이 가져가짐 (대여)
                        print(f"자리 {spot_id}에서 우산이 가져가짐.")
                        umbrella_box.update_spot_status(spot_id, False, None) 
                        
                        last_detected_user = None
                        no_person_count = 0 
                        if(current_system_state == STATE_UMBRELLA_ACTIVITY):
                            current_system_state = STATE_IDLE 
                
            time.sleep(0.5) 
            
    except KeyboardInterrupt:
        print("프로그램 종료 요청.")
    finally:
        hardware_manager.cleanup_hardware()
        print("하드웨어 정리 완료. 프로그램 종료.")

if __name__ == "__main__":
    main_loop()
