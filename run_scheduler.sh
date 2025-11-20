#!/bin/bash

# 脚本用于运行定时任务
# 步骤包括进入项目目录，激活pipenv环境，运行python脚本

# 进入项目主目录
cd "$(dirname "$0")"

# 检查pipenv是否安装
if ! command -v pipenv &> /dev/null
then
    echo "pipenv 未安装，请先安装 pipenv"
    exit 1
fi

# 从.env文件读取token
if [ -f ".env" ]; then
    export $(cat .env | xargs)
else
    echo "错误：找不到 .env 文件"
    exit 1
fi

# 检查DOT_CALENDAR_TOKEN是否存在
if [ -z "$DOT_CALENDAR_TOKEN" ]; then
    echo "错误：.env 文件中未设置 DOT_CALENDAR_TOKEN"
    exit 1
fi

# 通过pipenv运行Python脚本
pipenv run python main.py --token $DOT_CALENDAR_TOKEN --dotsync 1