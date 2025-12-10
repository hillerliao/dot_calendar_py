#!/bin/bash

# 进入项目主目录
cd "$(dirname "$0")/.."

# 检查pipenv是否安装 (using full path)
if [ ! -x "$HOME/.local/bin/pipenv" ]; then
    echo "pipenv 未安装，请先安装 pipenv"
    echo "Expected location: $HOME/.local/bin/pipenv"
    exit 1
fi

# Use the full path for pipenv
PIPENV_CMD="$HOME/.local/bin/pipenv"

# 从.env文件读取token
# 从.env文件读取token（忽略注释行和空行）
if [ -f ".env" ]; then
    while IFS= read -r line; do
        # 跳过注释行和空行
        [[ $line =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        # 只导出包含=的行
        if [[ $line == *"="* ]]; then
            export "$line"
        fi
    done < .env
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
$PIPENV_CMD run python src/main.py --token $DOT_CALENDAR_TOKEN --dotsync 1