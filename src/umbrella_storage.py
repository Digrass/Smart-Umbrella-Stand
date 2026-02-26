# umbrella_storage.py

class UmbrellaStorage:
    """
    우산 보관함의 각 자리 상태를 관리하는 클래스 (2명 사용자, 고정 자리).
    User A는 Spot 1, User B는 Spot 2를 사용한다고 가정합니다.
    """

    def __init__(self):
        # 각 사용자의 자리 정보를 직접 매핑합니다.
        # user_A -> spot 1
        # user_B -> spot 2
        self.user_spot_map = {
            "user_A": 1,
            "user_B": 2
        }
        
        # 각 자리의 상태를 저장하는 딕셔너리
        # 키는 spot_id (1부터 시작), 값은 상태 딕셔너리
        self.spots = {
            1: {"status": False, "user": None, "previous_status": False},
            2: {"status": False, "user": None, "previous_status": False}
        }
        self.num_spots = len(self.spots) # 자리 개수는 딕셔너리 크기

    def _get_spot_index(self, spot_id):
        """내부용: spot_id 유효성 검사."""
        if spot_id not in self.spots:
            return None
        return spot_id # 여기서는 딕셔너리 키이므로 그대로 반환

    def update_spot_status(self, spot_id, new_status, user_id=None):
        """특정 자리의 우산 유무를 업데이트하고, 필요시 user_id를 할당합니다."""
        spot_idx = self._get_spot_index(spot_id)
        if spot_idx is None:
            return False
        
        # 사용자 ID 유효성 검사 (고정된 자리에 맞는지)
        if user_id and self.user_spot_map.get(user_id) != spot_id:
            # 해당 사용자는 이 자리에 우산을 놓을 수 없습니다.
            # 또는, 우산을 가져가는 상황에서는 user_id가 None일 수 있으므로 허용
            if new_status: # 우산을 놓는 상황일 때만 체크
                 print(f"Warning: User {user_id} cannot use spot {spot_id}.")
                 return False

        current_spot = self.spots[spot_idx]
        current_spot["previous_status"] = current_spot["status"]
        current_spot["status"] = new_status

        if new_status:  # 우산이 새로 들어온 경우
            current_spot["user"] = user_id
        else:  # 우산이 가져가진 경우
            current_spot["user"] = None 
        
        return True

    def get_spot_status(self, spot_id):
        """특정 자리의 현재 우산 유무 상태를 반환합니다."""
        spot_idx = self._get_spot_index(spot_id)
        if spot_idx is None:
            return None
        
        return self.spots[spot_idx]["status"]

    def get_user_umbrella_spot(self, user_id):
        """주어진 user_id가 우산을 놓은 spot_id를 찾아 반환합니다."""
        # 고정된 자리이므로 맵에서 바로 찾아 반환
        return self.user_spot_map.get(user_id)


    # 이 함수는 이제 필요하지 않습니다. 각 사용자는 자신의 고정된 자리를 압니다.
    # def get_empty_spot_id(self):
    #     """비어있는 자리 중 첫 번째 자리의 spot_id를 반환합니다."""
    #     for spot_id, spot_data in self.spots.items():
    #         if not spot_data["status"]:
    #             return spot_id
    #     return None


    def has_umbrella_arrived(self, spot_id):
        """특정 자리에 우산이 새로 들어왔는지 확인합니다."""
        spot_idx = self._get_spot_index(spot_id)
        if spot_idx is None:
            return False
        
        current_spot = self.spots[spot_idx]
        return current_spot["status"] is True and current_spot["previous_status"] is False

    def has_umbrella_taken(self, spot_id):
        """특정 자리에서 우산이 가져가졌는지 확인합니다."""
        spot_idx = self._get_spot_index(spot_id)
        if spot_idx is None:
            return False
        
        current_spot = self.spots[spot_idx]
        return current_spot["status"] is False and current_spot["previous_status"] is True

    def reset_spot(self, spot_id):
        """특정 자리의 상태를 초기화합니다 (우산 없음, 사용자 없음)."""
        spot_idx = self._get_spot_index(spot_id)
        if spot_idx is None:
            return False
        
        current_spot = self.spots[spot_idx]
        current_spot["status"] = False
        current_spot["user"] = None
        current_spot["previous_status"] = False
        return True

    def get_all_spot_statuses(self):
        """모든 자리의 현재 상태를 반환합니다."""
        return {spot_id: {"status": data["status"], "user": data["user"]} for spot_id, data in self.spots.items()}