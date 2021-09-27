# ICVRCAutonomousDriving

#### 介绍
Python Implementation of Autunomous Driving Simulation

![high speed overtake](images/70km.gif)

![overtake example](images/50km.gif)

![当前最高得分](images/144.png)

#### 软件架构
包含感知、决策、规划、控制相关部分


#### 安装教程
git clone git@gitee.com:icvrc2021-neu/icvrcautonomous-driving.git 到本地，可进行开发.

# 操作查询

## 分支操作
`务必养成良好习惯`

#### 创建分支
`创建新分支并切换`
git checkout -b dev || 也可以先开发(比如直接改了master)，准备切分支时才new新分支，此时更改会都转移到新分支上
`提交新分支到远程`

git push --set-upstream origin dev

#### 合并分支
`开发结束后测试稳定即可合并到master`
1. git checkout master

2. git merge xld-control-pid

3. 必要时候解决冲突文件，注意注释后的代码合并进来不会提示。。。

#### 删除分支
1.1.查看本地分支 git branch 

1.2.查看远程分支 git branch -r

2.删除本地分支 
git branch -D xld-control-pid

3.删除远程分支 
git push origin --delete xld-control-pid

## 版本管理

#### 强制回退
`删除中间所有错误提交`
git reset --hard version-number

git reset version-number

`回退到上一个版本 不加^会有原地恢复的问题`
git revert HEAD







