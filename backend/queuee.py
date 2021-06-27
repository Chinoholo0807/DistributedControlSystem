import heapq
import threading


from service_object import *

class Queuee:
    def __init__(self) -> None:
        self.wait_count = 0
        self.index = 0
        self.wait_queue = []
        self.wait_lock = threading.Lock()

        self.service_queue = {} # 设计成字典类型，通过room_id访问
        self.service_lock = threading.Lock()
    
    # 创建服务对象
    @staticmethod
    def create_service_object(room_id,cur_temp,cur_speed,target_temp,target_speed):
        service_object = ServiceObject()
        service_object.init_room_id(room_id=room_id)
        service_object.init_servive_start_time()
        service_object.init_current_temp_and_speed(cur_temp=cur_temp,cur_speed=cur_speed)
        service_object.init_target(target_temp=target_temp,speed=target_speed)
        service_object.init_fee()
        return service_object
    
    # 将服务对象加入等待/待调度队列
    def add_into_wait_queue(self, service_object:ServiceObject):    
        with self.wait_lock:
            self.wait_count += 1
            heapq.heappush(
                self.wait_queue,(
                    service_object.priority,    # 优先级
                    self.index,     # 加入顺序
                    service_object      # 加入对象
                )
            )
            self.index += 1
        return True
    
    # 从等待/待调度队列中取得优先级最高的服务对象
    def get_from_wait_queue(self):
        with self.wait_lock:
            service_objects = heapq.nsmallest(1, self.wait_queue)
            if not service_objects:
                return None
            return service_objects[0][-1]
    
    # 把等待/待调度队列中优先级最高的服务对象弹出
    def pop_wait_queue(self):    
        with self.wait_lock:
            if self.wait_count == 0:
                return None
            self.wait_count -= 1
            service_object = heapq.heappop(self.wait_queue)[-1]
            service_object.wait_clock = 0  # 清空等待时长
        return service_object
    
    # 把服务对象加入到服务队列中
    def add_into_service_queue(self,service_object:ServiceObject):
        with self.service_lock:
            service_object.current_speed = service_object.target_speed
            self.service_queue[service_object.room_id] = service_object
            # 初始化时钟
            service_object.wait_clock = 0
            service_object.service_clock = 0
            service_object.start_serve()
        
        return True
    
    # 把房间id为room_id的服务对象从服务队列中弹出
    def pop_service_by_room_id(self, room_id):
        with self.service_lock:
            service_object = self.service_queue.pop(room_id)
            # 初始化时钟
            service_object.wait_clock = 0
            service_object.service_clock = 0
            service_object.stop_serve()
        return service_object
    
    # 得到服务队列中优先级最低的一个服务对象
    def get_service_object_with_lowest_priority_from_service_queue(self):
        #先找到优先级最低的一组服务对象
        objects_with_lowest_priority = []
        with self.service_lock:
            lowest_priority = None
            for room_id in self.service_queue:
                if lowest_priority is None:
                    lowest_priority = self.service_queue[room_id].priority
                    objects_with_lowest_priority.append(self.service_queue[room_id])
                elif lowest_priority < self.service_queue[room_id].priority:  
                    lowest_priority = self.service_queue[room_id].priority
                    objects_with_lowest_priority.clear()
                    objects_with_lowest_priority.append(self.service_queue[room_id])
                elif lowest_priority == self.service_queue[room_id].priority:
                    objects_with_lowest_priority.append(self.service_queue[room_id])
        # 在里面找到服务时间最长的一个
        object_with_longest_service_time= None
        for object in objects_with_lowest_priority:
            if object_with_longest_service_time is None:
                object_with_longest_service_time = object
            elif object_with_longest_service_time.service_clock < object.service_clock:
                object_with_longest_service_time = object

        return object_with_longest_service_time
