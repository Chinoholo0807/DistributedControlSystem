from sqlalchemy.sql.expression import false
from const import INIT_TEMP
from const import DEFAULT_TMP, FEE_PER_KWH, KWH_PER_MIN, POWER_OFF_TMP_PER_MIN, TMP_PER_MIN
from database import *
import threading
from time import sleep
from queuee import Queuee
from service_object import ServiceObject
from rooom import Rooom

class Scheduler:
    def __init__(self) -> None:
        self.mode = 'cold'
        self.fee_rate = 1.0
        self.temp_section = [18,25,25,30]
        self.default_temp = 25
        self.default_speed = 'MID'
        self.schedule_num = 3
        self.SLAVE_NUM = 4
        self.RR_SLOT = 120   #时间片调度间隔：两分钟

        self.queue = Queuee()
        self.max_object_num = 3

        self.rooms = {}
        for i in range(self.SLAVE_NUM):
            self.rooms[100+i+1] = Rooom(room_id=100+i+1,current_temp=INIT_TEMP[100+i+1])

        # 调度队列
        self.blowing_list = []
        self.schedule_queue = []

    # 增加NewStatistics中的各种记录字段数
    def add_record(self,record_name):
        currentTime=datetime.datetime.now().strftime('%Y-%m-%d')
        startTime=datetime.datetime.strptime(currentTime+' 00:00:00','%Y-%m-%d %H:%M:%S')
        endTime=datetime.datetime.strptime(currentTime+' 23:59:59','%Y-%m-%d %H:%M:%S')

        ans = NewStatistics.query.filter(startTime<=NewStatistics.dateTime).filter(NewStatistics.dateTime<=endTime).first()
        
        if ans is None:
            # 在NewStatistics中创建一个新的记录
            db.session.add(NewStatistics(totalNum=1,satisfyNum=0,scheduledNum=0,RDRNum=0,totalFee=0.0))
            db.session.commit()
        else:
            if record_name == 'scheduledNum':
                NewStatistics.query.filter(NewStatistics.id==ans.id).update({
                                'scheduledNum':ans.scheduledNum+1,
                })
            elif record_name == 'satisfyNum':
                NewStatistics.query.filter(NewStatistics.id==ans.id).update({
                                'satisfyNum':ans.satisfyNum+1,
                })
            elif record_name == 'totalNum':
                NewStatistics.query.filter(NewStatistics.id==ans.id).update({
                                'totalNum':ans.totalNum+1,
                })
            db.session.commit()


    # 更新服务时间、等待时间、费用、当前温度
    def update(self):

        mode_factor = -1 if self.mode == 'cold' else 1

        # 更新等待时间
        with self.queue.wait_lock:
            for item in self.queue.wait_queue:
                item[-1].wait_clock += 1
        # 更新循环时间
        with self.queue.service_lock:
            for room_id in self.queue.service_queue:
                self.queue.service_queue[room_id].service_clock += 1
        # 更新费用和当前温度
        with self.queue.service_lock:
            for room_id in self.rooms:
                # print('room_id = ',room_id)
                if room_id in self.queue.service_queue:
                    # 更新前的温度
                    previous_temp=self.rooms[room_id].current_temp
                    # 更新温度
                    self.rooms[room_id].current_temp += TMP_PER_MIN[self.queue.service_queue[room_id].current_speed] / 60 * mode_factor
                    # 更新后的温度
                    current_temp=self.rooms[room_id].current_temp
                    # 目标温度
                    target_temp=self.rooms[room_id].target_temp
                    # 更新费用
                    self.rooms[room_id].fee += KWH_PER_MIN[self.queue.service_queue[room_id].current_speed] / 60 * self.fee_rate
                    # 如果目标温度在更新前后的温度之间,说明达到了目标温度
                    if previous_temp <= target_temp <= current_temp or previous_temp >= target_temp >= current_temp:
                        self.add_record('satisfyNum')

                    Room.query.filter(Room.room_id == room_id).update({
                        "mode":self.mode,
                        "speed":self.queue.service_queue[room_id].current_speed,
                        "current_temp":self.rooms[room_id].current_temp,
                        "target_temp":self.rooms[room_id].target_temp,
                        "served_time":self.queue.service_queue[room_id].service_clock,
                        "fee":self.rooms[room_id].fee,
                        "state":"SENDING"
                    })
                elif self.rooms[room_id].current_temp * mode_factor > INIT_TEMP[room_id]* mode_factor:
                    self.rooms[room_id].current_temp -= POWER_OFF_TMP_PER_MIN /60 * mode_factor
                    Room.query.filter(Room.room_id == room_id).update({
                        "mode":self.mode,
                        "speed":"",
                        "current_temp":self.rooms[room_id].current_temp,
                        "target_temp":self.rooms[room_id].target_temp,
                        "served_time":0,
                        "fee":self.rooms[room_id].fee,
                        "state":"NOT SENDING"
                    })
                db.session.commit()
        

    # 调度
    def schedule(self):  
        while True:
            sleep(1)
            self.update()
            
            object = self.queue.get_from_wait_queue()
            if object is None:
                # 等待队列为空
                continue
            elif len(self.queue.service_queue)< self.max_object_num:
                # 等待队列不为空 且 服务队列仍然有空位
                self.add_record('scheduledNum')
                self.queue.pop_wait_queue()
                self.queue.add_into_service_queue(object)
                self.rooms[object.room_id].start_service()
                self.rooms[object.room_id].power_on()
                self.rooms[object.room_id].current_speed=self.rooms[object.room_id].target_speed
            else:
                # 服务队列已满
                object_with_lowest_priority = self.queue.get_service_object_with_lowest_priority_from_service_queue()

                if object.priority < object_with_lowest_priority.priority:
                    # 优先级调度
                    print('优先级调度')
                    self.add_record('scheduledNum')
                    self.queue.pop_wait_queue()
                    self.queue.add_into_service_queue(object)
                    self.rooms[object.room_id].power_on()
                    self.rooms[object.room_id].current_speed=self.rooms[object.room_id].target_speed
                    if len(self.queue.service_queue) != self.max_object_num:
                        self.queue.pop_service_by_room_id(object_with_lowest_priority.room_id)
                        self.queue.add_into_wait_queue(object_with_lowest_priority)
                        self.rooms[object_with_lowest_priority.room_id].power_off()
                        fee_this_time = self.rooms[object_with_lowest_priority.room_id].get_rdr_fee()
                        db.session.add(RoomRecode(
                            room_id=object_with_lowest_priority.room_id,
                            start_time=self.rooms[object_with_lowest_priority.room_id].start_time,
                            speed=self.rooms[object_with_lowest_priority.room_id].current_speed,
                            fee=fee_this_time,
                            times_used=1
                            ))
                        db.session.commit()
                        self.rooms[object_with_lowest_priority.room_id].current_speed = None
                elif object.priority == object_with_lowest_priority.priority:
                    # 时间片轮转
                    if object.wait_clock >= self.RR_SLOT:  # 等待时间已满，强行替换
                        print('时间片调度')
                        self.add_record('scheduledNum')
                        self.queue.pop_wait_queue()
                        self.queue.add_into_service_queue(object)
                        self.rooms[object.room_id].power_on()
                        self.rooms[object.room_id].current_speed=self.rooms[object.room_id].target_speed
                        if len(self.queue.service_queue) != self.max_object_num:
                            self.queue.pop_service_by_room_id(object_with_lowest_priority.room_id)
                            self.queue.add_into_wait_queue(object_with_lowest_priority)
                            self.rooms[object_with_lowest_priority.room_id].power_off()
                            fee_this_time = self.rooms[object_with_lowest_priority.room_id].get_rdr_fee()
                            db.session.add(RoomRecode(
                                room_id=object_with_lowest_priority.room_id,
                                start_time=self.rooms[object_with_lowest_priority.room_id].start_time,
                                speed=self.rooms[object_with_lowest_priority.room_id].current_speed,
                                fee=fee_this_time,
                                times_used=1
                                ))
                            db.session.commit()
                            self.rooms[object_with_lowest_priority.room_id].current_speed = None

    # 设置参数
    def set_para(self,mode,fee_rate,temp_section,default_temp,schedule_num):
        self.mode = mode
        self.fee_rate = fee_rate
        self.temp_section = temp_section
        self.default_temp = default_temp
        self.schedule_num = schedule_num
    
    # 获取房间状态
    def get_slave_state(self,roomId):
        print('roomid = ',roomId)
        if 100 < roomId and roomId < 100 + self.SLAVE_NUM+1:
            return self.rooms[roomId].get_state()
        return {}
    
    # 处理开机、关机、调温、调风请求
    def deal_with_require(self, roomId, targetTemp,targetSpeed,acState):

        tempSectionLow=self.temp_section[0] if self.mode == 'cold' else self.temp_section[2]
        tempSectionHigh=self.temp_section[1] if self.mode == 'cold' else self.temp_section[3]

        if tempSectionLow > targetTemp or tempSectionHigh < targetTemp:
            return False

        if acState == 'on':
            # 送风
            # if self.rooms[roomId].power == False:
            #     self.rooms[roomId].power_on()
            # 当处于送风状态时，将目标温度和目标风速信息写入数据库
            # 并且使用空调次数+1
            self.add_record('totalNum')
            db.session.add(TempSpeed(currentTemp=targetTemp,currentSpeed=targetSpeed))
            db.session.commit()

            if targetSpeed == self.rooms[roomId].get_target_speed():
                # 说明是调温指令
                self.rooms[roomId].set_target_temp(targetTemp)
                print('调温')
                self.make_service_object(self.rooms[roomId])
            else:
                # 说明是调风指令
                self.rooms[roomId].set_target_speed(targetSpeed)
                self.rooms[roomId].set_target_temp(targetTemp)
                print('调风')
                self.make_service_object(self.rooms[roomId])
        else:
            # 不送风
            self.rooms[roomId].power_off()
            if roomId in self.queue.service_queue:
                self.queue.pop_service_by_room_id(roomId)
                self.rooms[roomId].power_off()
                fee_this_time = self.rooms[roomId].get_rdr_fee()
                db.session.add(RoomRecode(
                    room_id=roomId,
                    start_time=self.rooms[roomId].start_time,
                    speed=self.rooms[roomId].current_speed,
                    fee=fee_this_time,
                    times_used=1
                    ))
                db.session.commit()
                self.rooms[roomId].current_speed = None
                # del self.queue.service_queue[roomId]
            for index, wait_obi in enumerate(self.queue.wait_queue):
                if wait_obi[-1].room_id == roomId:
                    del self.queue.wait_queue[index]
            print('不送风')
        return True

    # 创建服务对象,并加入等待队列
    def make_service_object(self,rooom:Rooom):
        object = self.queue.create_service_object(rooom.room_id,rooom.current_temp,rooom.current_speed,rooom.target_temp,rooom.target_speed)
        self.queue.add_into_wait_queue(object)
