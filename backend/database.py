from app import *

from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80), nullable=True)
    type = db.Column(db.Enum('receptionist','manager','administrator','room'))
    times_used = db.Column(db.Integer, default=1)
    room_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.Enum('in','out'), default='out')

    def __str__(self) -> str:
        if(self.type != 'room'):
            return 'id:{0},username:{1},password:{2},type:{3}'.format(
                self.id,self.username,self.password,self.type)
        else:
            return 'id:{0},username:{1},password:{2},type:{3},times_used{4},status:{5},room_id:{6}'.format(
                self.id,self.username,self.password,self.type,self.times_used,self.status,self.room_id)

    def __repr__(self) -> str:
        return self.__str__()

class RoomRecode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.datetime.now)
    end_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    speed = db.Column(db.Enum("HIGH", "MID", "LOW"))
    fee = db.Column(db.Float, default=0.0)
    times_used = db.Column(db.Integer, nullable=True)

    def __str__(self) -> str:
        return 'id:{0},room_id:{1},start_time:{2},end_time:{3},speed:{4},fee:{5},times_used:{6}'.format(
            self.id,self.room_id,self.start_time,self.end_time,self.speed,self.fee,self.times_used)

    def __repr__(self) -> str:
        return self.__str__()

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, nullable=True)              # 房间id
    mode = db.Column(db.String(80))                             # 冷热模式
    speed = db.Column(db.Enum("HIGH", "MID", "LOW", ""))    # 当前风速
    current_temp = db.Column(db.Float, nullable=True)         # 当前温度
    target_temp = db.Column(db.Float, nullable=True)          # 目标温度
    state = db.Column(db.Enum("SENDING", "NOT SENDING"))         # 是否送风
    served_time = db.Column(db.Integer, nullable=True)     # 服务时间
    fee = db.Column(db.Float, nullable=True)        #费用

class Statistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    totalNum = db.Column(db.Integer)

# 各种计数
class NewStatistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dateTime = db.Column(db.DateTime, default=datetime.datetime.now)
    totalNum = db.Column(db.Integer)
    satisfyNum = db.Column(db.Integer, nullable=True)
    scheduledNum = db.Column(db.Integer, nullable=True)
    RDRNum = db.Column(db.Integer, nullable=True)
    totalFee = db.Column(db.Float, default=0.0)

    def __str__(self) -> str:
        return 'id:{0},dateTime:{1},totalNum:{2},satisfyNum:{3},scheduledNum:{4},RDRNum:{5},totalFee:{6}'.format(
            self.id,self.dateTime,self.totalNum,self.satisfyNum,self.scheduledNum,self.RDRNum,self.totalFee)

    def __repr__(self) -> str:
        return self.__str__()

class TempSpeed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dateTime = db.Column(db.DateTime, default=datetime.datetime.now)
    currentTemp = db.Column(db.Integer, nullable=True)
    currentSpeed = db.Column(db.Enum("HIGH", "MID", "LOW", ""))

    def __str__(self) -> str:
        return 'id:{0},dataTime:{1},currentTemp:{2},currentSpeed:{3}'.format(
            self.id,self.dateTime,self.currentTemp,self.currentSpeed
        )
    
    def __repr__(self) -> str:
        return self.__str__()



def db_init():
    db.drop_all()
    db.create_all()
    db.session.add(User(username='receptionist_1',password='receptionist',type='receptionist'))
    db.session.add(User(username='manager_1',password='manager',type='manager'))
    db.session.add(User(username='administrator_1',password='administrator',type='administrator'))
    db.session.add(User(username='room_1',password='room',type='room',room_id=101))
    db.session.add(User(username='room_2',password='room',type='room',room_id=102))
    db.session.add(User(username='room_3',password='room',type='room',room_id=103))
    db.session.add(User(username='room_4',password='room',type='room',room_id=104))


    # 测试数据2
    db.session.add(Room(room_id=101,mode='cold',speed='',current_temp=32,target_temp=25,state='NOT SENDING',served_time=0,fee=0))
    db.session.add(Room(room_id=102,mode='cold',speed='',current_temp=28,target_temp=25,state='NOT SENDING',served_time=0,fee=0))
    db.session.add(Room(room_id=103,mode='cold',speed='',current_temp=30,target_temp=25,state='NOT SENDING',served_time=0,fee=0))
    db.session.add(Room(room_id=104,mode='cold',speed='',current_temp=29,target_temp=25,state='NOT SENDING',served_time=0,fee=0))

    # 测试数据3
    dates=['2021-06-22','2021-06-23','2021-06-24','2021-06-25']
    format_dates=[]
    for date in dates:
        format_dates.append(datetime.datetime.strptime(date,'%Y-%m-%d'))
    db.session.add(NewStatistics(dateTime=format_dates[0],totalNum=23,satisfyNum=2,scheduledNum=28,RDRNum=3,totalFee=15.8))
    db.session.add(NewStatistics(dateTime=format_dates[1],totalNum=12,satisfyNum=0,scheduledNum=15,RDRNum=13,totalFee=16.8))
    db.session.add(NewStatistics(dateTime=format_dates[2],totalNum=36,satisfyNum=3,scheduledNum=38,RDRNum=0,totalFee=17.8))
    db.session.add(NewStatistics(dateTime=format_dates[3],totalNum=32,satisfyNum=1,scheduledNum=40,RDRNum=21,totalFee=18.8))
    
    # 测试数据4
    dates=['2021-06-22','2021-06-23','2021-06-24','2021-06-25']
    format_dates=[]
    for date in dates:
        format_dates.append(datetime.datetime.strptime(date,'%Y-%m-%d'))
    db.session.add(TempSpeed(dateTime=format_dates[0],currentTemp=24,currentSpeed='HIGH'))
    db.session.add(TempSpeed(dateTime=format_dates[1],currentTemp=23,currentSpeed='MID'))
    db.session.add(TempSpeed(dateTime=format_dates[2],currentTemp=19,currentSpeed='HIGH'))
    db.session.add(TempSpeed(dateTime=format_dates[2],currentTemp=20,currentSpeed='MID'))
    db.session.add(TempSpeed(dateTime=format_dates[3],currentTemp=22,currentSpeed='LOW'))



    db.session.commit()