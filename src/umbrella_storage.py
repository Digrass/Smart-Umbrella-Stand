# umbrella_storage.py

class UmbrellaStorage:
    
    
    #User A는 Spot 1, User B는 Spot 2를 사용
    def __init__(self):
        self.user_spot_map = {
            "user_A": 1,
            "user_B": 2
        }
        
        self.spots = {
            1: {"status": False, "user": None, "previous_status": False},
            2: {"status": False, "user": None, "previous_status": False}
        }
        self.num_spots = len(self.spots)

    def _get_spot_index(self, spot_id):
        if spot_id not in self.spots:
            return None
        return spot_id

    #우산 보관 상태 업데이트
    def update_spot_status(self, spot_id, new_status, user_id=None):
        spot_idx = self._get_spot_index(spot_id)
        if spot_idx is None:
            return False
        
        # 사용자 ID 유효성 검사
        if user_id and self.user_spot_map.get(user_id) != spot_id:
            if new_status: #우산이 새로 들어왔을 때에만 확인
                 print(f"Warning: User {user_id} cannot use spot {spot_id}.")
                 return False

        current_spot = self.spots[spot_idx]
        current_spot["previous_status"] = current_spot["status"]
        current_spot["status"] = new_status

        if new_status:  # 우산이 새로 들어온 경우
            current_spot["user"] = user_id
        else:  # 우산이 사라진 경우
            current_spot["user"] = None 
        
        return True
    #우산 보관 상태 반환
    def get_spot_status(self, spot_id):
        spot_idx = self._get_spot_index(spot_id)
        if spot_idx is None:
            return None
        
        return self.spots[spot_idx]["status"]

    def get_user_umbrella_spot(self, user_id):
        return self.user_spot_map.get(user_id)

    #우산이 새로 들어왔는지 확인
    def has_umbrella_arrived(self, spot_id):
        spot_idx = self._get_spot_index(spot_id)
        if spot_idx is None:
            return False
        
        current_spot = self.spots[spot_idx]
        return current_spot["status"] is True and current_spot["previous_status"] is False

    #우산이 사라졌는지 확인
    def has_umbrella_taken(self, spot_id):
        spot_idx = self._get_spot_index(spot_id)
        if spot_idx is None:
            return False
        
        current_spot = self.spots[spot_idx]
        return current_spot["status"] is False and current_spot["previous_status"] is True

    def reset_spot(self, spot_id):
        spot_idx = self._get_spot_index(spot_id)
        if spot_idx is None:
            return False
        
        current_spot = self.spots[spot_idx]
        current_spot["status"] = False
        current_spot["user"] = None
        current_spot["previous_status"] = False
        return True

    def get_all_spot_statuses(self):
        return {spot_id: {"status": data["status"], "user": data["user"]} for spot_id, data in self.spots.items()}
