import datetime
from const import *

class ServiceObject:
    def __init__(self) -> None:
        self.room_id = None
        self.start_time = None

        self.current_temp = DEFAULT_TMP
        self.target_temp = DEFAULT_TMP

        self.current_speed = 'MID'
        self.target_speed = 'MID'

        self.fee = 0

        self.priority = 0  # 调度优先级
        self.wait_clock = 0  # 在服务队列里等待的时间
        self.service_clock = 0  # 队列服务时长
    
    def init_room_id(self,room_id):
        self.room_id = room_id
        return True

    def init_servive_start_time(self):
        self.start_time = datetime.datetime.now()
        return True
    
    def init_current_temp_and_speed(self,cur_temp,cur_speed):
        self.current_temp = cur_temp
        self.current_speed = cur_speed
        return True
    
    def init_fee(self):
        self.fee = 0
        return True
    
    def init_target(self, target_temp, speed):
        self.target_temp = target_temp
        self.target_speed = speed

        # 判断优先级
        if self.target_speed == 'HIGH':
            self.priority = 1
        elif self.target_speed == 'MID':
            self.priority = 2
        else:
            self.priority = 3
        # if self.target_speed is not None:
        #     if self.target_speed == 'HIGH':
        #         self.priority = 1
        #     elif self.target_speed == 'MID':
        #         self.priority = 2
        #     else:
        #         self.priority = 3
        # else:
        #     if self.speed == 'HIGH':
        #         self.priority = 1
        #     elif self.speed == 'MID':
        #         self.priority = 2
        #     else:
        #         self.priority = 3
        
        # if not self.target_temp:
        #     self.target_temp = self.current_temp
        # if not self.target_speed:
        #     self.target_speed = self.current_speed

    def start_serve(self):
        # 开始计费
        pass

    def stop_serve(self):
        # 停止计费
        pass