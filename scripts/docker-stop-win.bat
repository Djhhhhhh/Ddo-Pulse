@echo off
chcp 65001 >nul

:: Ddo-Pulse Docker 停止脚本 (Windows)

echo.
echo 🐳 Ddo-Pulse Docker 停止脚本 (Windows)
echo ====================================
echo.

set CONTAINER_NAME=ddo-pulse

:: 检测 Docker 是否安装
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装
    pause
    exit /b 1
)

:: 检测 Docker daemon 是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Docker daemon 未运行
    echo 容器可能已经停止
    pause
    exit /b 0
)

:: 停止并删除容器
docker ps -q -f "name=%CONTAINER_NAME%" 2>nul | findstr /r "." >nul
if %errorlevel% equ 0 (
    echo ⏹️  正在停止容器 %CONTAINER_NAME% ...
    docker stop %CONTAINER_NAME%
    docker rm %CONTAINER_NAME%
    echo.
    echo ✅ Ddo-Pulse 已停止
) else (
    docker ps -aq -f "name=%CONTAINER_NAME%" 2>nul | findstr /r "." >nul
    if %errorlevel% equ 0 (
        docker rm %CONTAINER_NAME%
        echo.
        echo ✅ 已清理停止的容器 %CONTAINER_NAME%
    ) else (
        echo ℹ️  容器 %CONTAINER_NAME% 不存在
    )
)

echo.
pause
