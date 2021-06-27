import datetime


class Rooom:
    def __init__(self,room_id, current_temp) -> None:
        self.power = False
        self.room_id = room_id
        self.current_temp = current_temp
        self.current_speed = None
        self.target_temp = None
        self.target_speed = None
        self.start_time = None
        self.last_fee = 0
        self.fee = 0
    
    # 送风
    def power_on(self):
        self.power = True
        return True

    # 没送风
    def power_off(self):
        self.power = False
        return True
    
    def set_target_temp(self,target_temp):
        self.target_temp = target_temp

    def set_target_speed(self, target_speed):
        self.target_speed = target_speed

    def get_target_speed(self):
        return self.target_speed

    def get_state(self):
        ret = {}
        ret['fee']=self.fee
        ret['currTemp']=self.current_temp
        ret['targetTemp']=self.target_temp
        ret['acState'] = 'on' if self.power == True else 'off'
        if ret['acState'] != 'off':
            ret['speed']=self.current_speed.lower()
        return ret

    def start_service(self):
        self.start_time = datetime.datetime.now()

    def get_rdr_fee(self):
        ans = self.fee - self.last_fee
        self.last_fee = self.fee
        return ans