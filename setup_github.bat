@echo off
echo 🔧 GitHub仓库配置脚本
echo.
echo 请先在GitHub创建Personal Access Token，然后输入：
echo.
set /p token="请输入您的GitHub Personal Access Token: "

if "%token%"=="" (
    echo ❌ Token不能为空！
    pause
    exit /b 1
)

echo.
echo 🔗 配置远程仓库...
git remote add origin https://%token%@github.com/Kirin-0321/audio-to-controller-vibration.git

echo.
echo 📤 推送到GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ 成功推送到GitHub！
    echo 🌐 仓库地址: https://github.com/Kirin-0321/audio-to-controller-vibration
) else (
    echo.
    echo ❌ 推送失败！请检查Token是否正确
)

echo.
pause
