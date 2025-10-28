#!/bin/bash

echo "========================================"
echo "YuketangAutoPlayer 打包脚本"
echo "========================================"
echo ""

# 检查是否存在 chromedriver.exe
if [ ! -f "chromedriver.exe" ]; then
    echo "[错误] 未找到 chromedriver.exe！"
    echo "请将 chromedriver.exe 放在项目根目录下"
    read -p "按回车键退出..."
    exit 1
fi

echo "[1/3] 安装打包依赖..."
uv pip install pyinstaller

echo ""
echo "[2/3] 开始打包..."
pyinstaller YuketangAutoPlayer.spec --clean

echo ""
if [ -f "dist/YuketangAutoPlayer.exe" ]; then
    echo "[3/3] 打包成功！"
    echo ""
    echo "输出文件: dist/YuketangAutoPlayer.exe"
    echo ""
    echo "使用说明:"
    echo "1. 将 dist/YuketangAutoPlayer.exe 复制到任意目录"
    echo "2. 首次运行会自动生成 config.ini 配置文件"
    echo "3. 编辑 config.ini 填写课程URL和Cookie"
    echo "4. 再次运行即可开始自动播放"
    echo ""
else
    echo "[错误] 打包失败！"
    echo "请检查控制台输出的错误信息"
fi

read -p "按回车键退出..."
