# ICVRCAutonomousDriving

#### 介绍
Python Implementation of Autunomous Driving Simulation

#### 软件架构
包含感知、决策、规划、控制相关部分

#### 安装教程
git clone git@gitee.com:icvrc2021-neu/icvrcautonomous-driving.git 到本地，可进行开发.

# 操作查询
## 分支操作
#### 创建分支
git checkout -b dev，这条命令把创建本地分支和切换到该分支的功能结合起来了，即基于当前分支master创建本地分支dev并切换到该分支下。

#### 删除分支
1.git branch 查看本地分支

2.删除本地分支 xld-control-pid。 
(1) git checkout xld-control-changelane 删除分支前先切换到其他分支 
(2) git branch -D xld-control-pid

3.查看远程分支 git branch -r

4.删除远程分支 git push origin --delete xld-control-pid END
