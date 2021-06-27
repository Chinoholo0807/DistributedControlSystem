# -*- coding utf-8 -*-

# 缺省房间温度
DEFAULT_TMP = 25

# 制冷模式温度范围：18-25 度
MIN_COLD_TMP = 18
MAX_COLD_TMP = 25

# 制热模式温度范围：25-30 度
MIN_HOT_TMP = 25
MAX_HOT_TMP = 30

# 计费标准：1 元/KWh
FEE_PER_KWH = 1

# 耗电标准：
# 高风：1 度/1 分钟
# 中风：1 度/2 分钟
# 低风：1 度/3 分钟
HIGH_SPEED_KWH_PER_MIN = 1
MID_SPEED_KWH_PER_MIN = 0.5
LOW_SPEED_KWH_PER_MIN = 0.33

KWH_PER_MIN = {
    'HIGH':1,
    'MID':0.5,
    'LOW':0.33
}

HIGH_SPEED_MIN_PER_KWH = 1
MID_SPEED_MIN_PER_KWH = 2
LOW_SPEED_MIN_PER_KWH = 3



# 高风模式每分钟变化 0.6度
# 中风模式下每分钟变化 0.5 度
# 低风模式每分钟变化 0.4 度
# 关机状态下，每分钟变化 0.5 度，直到变化到初始温度为止
POWER_OFF_TMP_PER_MIN = 0.5

LOW_SPEED_TMP_PER_MIN = 0.4
MID_SPEED_TMP_PER_MIN = 0.5
HIGH_SPEED_TMP_PER_MIN = 0.6

TMP_PER_MIN = {
    'LOW':0.4,
    'MID':0.5,
    'HIGH':0.6
}

INIT_TEMP = {
    101:32,
    102:28,
    103:30,
    104:29
}