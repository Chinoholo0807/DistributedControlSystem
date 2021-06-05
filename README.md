<!--
 * @Description: 
 * @Author: l
 * @Date: 2021-06-03 20:40:55
 * @LastEditors: l
 * @LastEditTime: 2021-06-03 20:46:27
 * @FilePath: \DistributedControlSystem\README.md
-->
# DistributedControlSystem

# back-end
这里是后端的分支

## 后端python依赖配置
在backend目录下，输入以下命令(如有担心与本地配置冲突，可以选择先创建虚拟环境)
```
pip install -r requirements.txt
```

## 数据库
数据库使用的是mysql


## 数据库初始化
    第一次运行时请运行main函数中的db_init()来初始化数据库。
    数据库相关配置在config.py中，建议你在本地mysql创建一个名为air，密码为123456的用户，并授予所有权限。同时创建一个名为air的数据库。