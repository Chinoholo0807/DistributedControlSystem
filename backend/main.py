import re
from threading import Thread
from app import *
from flask import request, jsonify
from database import *
from sqlalchemy import func
import utils
from scheduler import Scheduler
import datetime

scheduler = Scheduler()
t = Thread(target=scheduler.schedule)

# 登录 FINISH
@app.route('/auth/loginAdmin', methods=['POST'])
def login_admin():
    """
    userName
    password
    :return: {error:bool.
                role:str}  # room/administrator/manager/receptionist
    """

    params = request.get_json(force=True)
    print(request.path, " : ", params)
    params = request.get_json(force=True)
    # print(request.path, " : ", params)
    username = params['userName']
    password = params['password']
    # print(username, ',', password)

    ans = User.query.filter(User.username == username).filter(User.password == password).first()

    if ans is None:
        print('登录失败')
        return jsonify({'error': True})
    else:
        print('登录成功')
        ret = {'error': False, 'role': ans.type}
        if ret['role'] == 'room':
            attributes = {
                'defaultTemp':scheduler.default_temp,
                'defaultSpeed':scheduler.default_speed.lower(),
                'tempSectionLow':int(scheduler.temp_section[0] if scheduler.mode == 'cold' else scheduler.temp_section[2]),
                'tempSectionHigh':int(scheduler.temp_section[1] if scheduler.mode == 'cold' else scheduler.temp_section[3]),
                'roomId': ans.room_id,
                'mode':scheduler.mode
            }
            ret['attributes']=attributes
        return jsonify(ret)



# 这个暂时没什么用了 FINISH
@app.route('/auth/login', methods=['POST'])
def login():
    """
    登录
    :params:{
        username:str
        password:str
    }
    :return:{
        error: bool # 处理请求过程中是否发生错误，登录失败返回True，登录成功返回False
        type: str   # 类型:{'receptionist','manager','administrator','room'}
    }
    """
    params = request.get_json(force=True)
    # print(request.path, " : ", params)
    username = params['userName']
    password = params['password']
    # print(username, ',', password)
    query_list = [
        User.username == username,
        User.password == password
    ]
    print('标记1-----------------')
    ans = User.query.filter(*query_list).first()

    if ans is None:
        print('登录失败')
        return jsonify({'error': True})
    else:
        print('登录成功')
        return jsonify({'error': False, 'role': ans.type})
    

# 详单 FINISH
@app.route('/receptionist/getRDR', methods=['POST'])
def create_RDR():
    """前台开详单
    roomId:int
    :return: { RDR:{
                    startTime:str,
                    endTime:str,
                    speed:str,
                    fee:double } ,
                error:bool}
                
    """

    # 开一次详单,向NewStatistics表里当天所在行的RDRNum字段加一
    currentTime=datetime.datetime.now().strftime('%Y-%m-%d')
    startTime=datetime.datetime.strptime(currentTime+' 00:00:00','%Y-%m-%d %H:%M:%S')
    endTime=datetime.datetime.strptime(currentTime+' 23:59:59','%Y-%m-%d %H:%M:%S')

    ans = NewStatistics.query.filter(startTime<=NewStatistics.dateTime).filter(NewStatistics.dateTime<=endTime).first()
    
    if ans is None:
        # 在NewStatistics中创建一个新的记录
        db.session.add(NewStatistics(totalNum=0,satisfyNum=0,scheduledNum=0,RDRNum=1,totalFee=0.0))
        db.session.commit()
    else:
        NewStatistics.query.filter(NewStatistics.id==ans.id).update({
                        'RDRNum':ans.RDRNum+1,
        })
        db.session.commit()

    params = request.get_json(force=True)
    print(request.path, " : ", params)
    roomId=params['roomId']
    times_used = User.query.filter(User.room_id == roomId).first().times_used
    ans = RoomRecode.query.filter(RoomRecode.room_id == roomId).filter(RoomRecode.times_used == times_used).all()

    RDR = []
    start_time_list = []
    end_time_list = []
    speed_list = []
    fee_list = []
    for i in ans:
        # start_time_list.append(i.start_time)
        # end_time_list.append(i.end_time)
        # speed_list.append(i.speed)
        # fee_list.append(i.fee)
        RDR.append({
            'startTime':i.start_time,
            'endTime':i.end_time,
            'speed':i.speed,
            'fee':i.fee
        })

    return jsonify({'error': False,
                    'RDR': RDR})



# 账单 FINISH
@app.route('/receptionist/getBill', methods=['POST'])
def create_bill():
    """前台开账单
    roomId:int
    :return: { bill:{fee:double },
                error:bool }
    """

    params = request.get_json(force=True)
    print(request.path, " : ", params)
    roomId=params['roomId']
    times_used = User.query.filter(User.room_id == roomId).first().times_used
    fee = db.session.query(func.sum(RoomRecode.fee)).filter(RoomRecode.room_id == roomId).filter(RoomRecode.times_used == times_used).scalar()
    if fee is None:
        fee = 0

    return jsonify({'error': False,
                    'bill': {'fee': fee}})



# 开房 FINISH
@app.route('/receptionist/checkIn', methods=['POST'])
def check_in():
    """前台开房
    roomId
    :return: { idCard:str ,
                error:bool }
    """
    params = request.get_json(force=True)
    # print(request.path, " : ", params)
    roomId = params['roomId']
    # print(username, ',', password)
    query_list = [
        User.room_id == roomId,
        User.status == 'out'
    ]
    ans = User.query.filter(*query_list).first()

    if ans is None:
        return jsonify({'error': True})
    else:
        idCard = utils.random_str()
        User.query.filter(*query_list).update({
            'status':'in',
            'times_used':ans.times_used+1,
            'password':idCard
        })
        db.session.commit()
        return jsonify({'error': False, 'idCard': idCard})


# 退房 FINISH
@app.route('/receptionist/checkOut', methods=['POST'])
def check_out():
    """前台退房
    roomId:int
    :return: { error:bool }
    """

    params = request.get_json(force=True)
    # print(request.path, " : ", params)
    roomId = params['roomId']
    # print(username, ',', password)
    query_list = [
        User.room_id == roomId,
        User.status == 'in'
    ]
    ans = User.query.filter(*query_list).first()

    if ans is None:
        return jsonify({'error': True})
    else:
        User.query.filter(*query_list).update({
            'status':'out',
        })
        db.session.commit()
        return jsonify({'error': False})


@app.route('/manager/checkReport', methods=['POST'])
def check_report():
    """经理生成格式化报表
    startTime:str
    endTime:str
    :return: { error:bool,
                report:{ totalNum:int , 使用空调次数（每有一次送风请求，增加一次）
                        commonTemp:int , 最常使用的温度
                        commonSpeed:str , 最常使用的风速
                        satisfyNum:int , 到达目标温度的次数
                        scheduledNum:int, 被调度的次数
                        RDRNum:int , 生成RDR的次数
                        totalFee:double }}
    """

    params = request.get_json(force=True)
    print(request.path, " : ", params)

    # 时间格式暂时按照图片里的YYYY/MM/DD，如2021/06/25
    # 起止日期，为date类
    startTime=datetime.datetime.strptime(params['startTime'],'%Y-%m-%d')
    endTime=datetime.datetime.strptime(params['endTime']+' 23:59:59','%Y-%m-%d %H:%M:%S')


    # 筛选出日期位于startDate和endDate之间的行
    ans = NewStatistics.query.filter(startTime<NewStatistics.dateTime).filter(NewStatistics.dateTime<endTime).all()

    totalNumSum=0
    satisfyNumSum=0
    scheduledNumSum=0
    RDRNumSum=0
    totalFeeSum=0.0

    report={}
    for i in ans:
        date=i.dateTime.strftime('%Y-%m-%d')
        report[date]={
            'totalNum':i.totalNum,
            'satisfyNum':i.satisfyNum,
            'scheduledNum':i.scheduledNum,
            'RDRNum':i.RDRNum,
            'totalFee':i.totalFee,
        }
        totalNumSum+=i.totalNum
        satisfyNumSum+=i.satisfyNum
        scheduledNumSum+=i.scheduledNum
        RDRNumSum+=i.RDRNum
        totalFeeSum+=i.totalFee

    ans = TempSpeed.query.filter(startTime<TempSpeed.dateTime).filter(TempSpeed.dateTime<endTime).all()
    common_temp_dict={}
    common_speed_dict={}
    for i in ans:
        date=i.dateTime.strftime('%Y-%m-%d')
        if date not in common_temp_dict.keys():
            common_temp_dict[date]=[]
        common_temp_dict[date].append(i.currentTemp)

        if date not in common_speed_dict.keys():
            common_speed_dict[date]=[]
        common_speed_dict[date].append(i.currentSpeed)
            
    for date in common_temp_dict.keys():
        report[date]['commonTemp']=max(common_temp_dict[date],key=common_temp_dict[date].count)
    for date in common_speed_dict.keys():
        report[date]['commonSpeed']=max(common_speed_dict[date],key=common_speed_dict[date].count)

    report_list=[]
    for key,value in report.items():
        report_list.append({
            'dateTime':key,
            'totalNum':value['totalNum'],
            'commonTemp':value['commonTemp'],
            'commonSpeed':value['commonSpeed'],
            'satisfyNum':value['satisfyNum'],
            'scheduledNum':value['scheduledNum'],
            'RDRNum':value['RDRNum'],
            'totalFee':value['totalFee'] 
        })
        

    total_temp_list=[]
    total_speed_list=[]
    for i in common_temp_dict.values():
        total_temp_list.extend(i)
    for i in common_speed_dict.values():
        total_speed_list.extend(i)

    return jsonify({'error': False,
                    'report': report_list,
                    'reportTotal':{
                                'totalNum':totalNumSum,
                                'commonTemp':max(total_temp_list,key=total_temp_list.count),
                                'commonSpeed':max(total_speed_list,key=total_speed_list.count),
                                'satisfyNum':satisfyNumSum,
                                'scheduledNum':scheduledNumSum,
                                'RDRNum':RDRNumSum,
                                'totalFee':float('%.2f'%totalFeeSum) 
                    }})



# 管理员设置默认参数 FINISH
@app.route('/administrator/setDefaultParams', methods=['POST'])
def set_default_params():
    """管理员设置默认参数
    defaultMode:str {hot,cold}
    coldHigh:int 温度范围 4个数
    coldLow:int  
    hotHigh:int
    hotLow:int
    defaultTemp: int
    feeRate: double
    scheduledNum: int
    :return: {error:bool}
    """
    params = request.get_json(force=True)
    print(request.path, " : ", params)
    mode = params['defaultMode']
    # tempSection = params['tempSection']
    hotHigh = int(params['hotHigh'])
    hotLow = int(params['hotLow'])
    coldHigh = int(params['coldHigh'])
    coldLow = int(params['coldLow'])
    defaultTemp = int(params['defaultTemp'])
    feeRate = float(params['feeRate'])
    scheduleNum = int(params['scheduledNum'])

    scheduler.set_para(mode,feeRate,[coldLow,coldHigh,hotLow,hotHigh],defaultTemp,scheduleNum)

    print(request.path, " : ", params)
    return jsonify({'error': False})


# 管理员检查房间状态 FINISH
@app.route('/administrator/checkRoomsState', methods=['POST'])
def check_room_state():
    """管理员检查房间状态
    :return: { roomStates:[ roomState:
                           {roomId:int,
                            state:str, # on/off 是否送风
                            mode:str,
                            speed:str,
                            currTemp:int,
                            targetTemp:int
                            }],
                            error:bool }
    """
    ans = Room.query.all()


    roomsState = []
    for i in ans:
        isCheckIn = User.query.filter(User.room_id == i.room_id).first().status
        roomsState.append({
            'roomId': i.room_id,
            'isCheckIn': isCheckIn=='in',
            'state': i.state.lower(),
            'mode': i.mode,
            'speed': i.speed.lower(),
            'currTemp': i.current_temp,
            'targetTemp': i.target_temp,
            'servedTime': i.served_time,
            'fee':i.fee
        })

    return jsonify({
        'error': False,
        'roomsState': roomsState
    })


# 向房客发送房间信息 FINISH
@app.route('/room/updateRoomState', methods=['POST'])
def update_room_state():
    """
    客户定期请求空调信息
    :params:{
        roomId:int          # 房间号
    }
    :return: {
        roomState:{
            speed:str,      # 风速：{"HIGH", "MID", "LOW"}
            currTemp:int,   # 当前温度
            targetTemp:int, # 目标温度
            fee:double,     # 费用
            acState:str     # 空调状态：{"On","Off","WaitForSchedul","Sleep"}
        },
        error:bool          # 处理请求过程是否发生错误，一般回送False
    }
    """
    params = request.get_json(force=True)
    print(request.path, " : ", params)
    roomId = int(params['roomId'])
    roomState = scheduler.get_slave_state(roomId=roomId)
    return jsonify({
        'error': False,
        'roomState': roomState
    })

# 处理房客的开关机、调温、调风请求 FINISH
@app.route('/room/changeRoomState', methods=['POST'])
def change_room_state():
    """
    客户发送开关机、送风、调温请求
    params:{
        roomId:int,         # 房间号
        targetTemp:int,     # 目标温度
        targetSpeed:str,    # 目标风速：{"HIGH", "MID", "LOW"}
        acState:str         # 开机/关机：{"On", "Off"}
    }
    :return: {
        error:bool          # 处理请求过程是否发生错误，一般回送False
    }
    """
    
    params = request.get_json(force=True)
    print(request.path, " : ", params)
    roomId = int(params['roomId'])
    targetTemp = int(params['targetTemp'])
    targetSpeed = params['targetSpeed'].upper()
    acState = params['acState']
    print(request.path, " : ", params)

    ret = scheduler.deal_with_require(roomId, targetTemp,targetSpeed,acState)

    return jsonify({
        'error': not ret
    })


if __name__ == '__main__':
    db_init()  # 这行代码，如果数据库没有发生变化，则跑一次即可
    t.start()
    app.run(port=5000, debug=True, host='0.0.0.0')