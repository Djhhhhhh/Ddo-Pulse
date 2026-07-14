@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Ddo-Pulse Docker 启动脚本 (Windows)

echo.
echo 🐳 Ddo-Pulse Docker 启动脚本 (Windows)
echo ====================================
echo.

set IMAGE_NAME=ddo-pulse
set CONTAINER_NAME=ddo-pulse

:: 设置端口
if "%DDO_PULSE_PORT%"=="" (
    set HOST_PORT=8765
) else (
    set HOST_PORT=%DDO_PULSE_PORT%
)

if "%DDO_PULSE_API_PORT%"=="" (
    set API_PORT=8765
) else (
    set API_PORT=%DDO_PULSE_API_PORT%
)

:: 检测 Docker 是否安装
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装
    echo.
    echo 请先安装 Docker Desktop for Windows:
    echo   https://docs.docker.com/desktop/install/windows-install/
    echo.
    pause
    exit /b 1
)

:: 检测 Docker daemon 是否运行
echo 🔍 检测 Docker daemon...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Docker daemon 未运行
    echo.

    :: 尝试启动 Docker Desktop
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        echo 🚀 正在启动 Docker Desktop...
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

        :: 等待 Docker daemon 启动
        echo ⏳ 等待 Docker daemon 启动...
        set RETRIES=0
        :WAIT_DOCKER
        docker info >nul 2>&1
        if %errorlevel% equ 0 (
            echo ✅ Docker daemon 已启动
            goto DOCKER_STARTED
        )

        set /a RETRIES+=1
        if !RETRIES! geq 30 (
            echo ❌ Docker daemon 启动超时
            echo.
            echo 请手动启动 Docker Desktop，然后重试
            pause
            exit /b 1
        )

        timeout /t 2 /nobreak >nul
        goto WAIT_DOCKER

        :DOCKER_STARTED
    ) else (
        echo ❌ 未找到 Docker Desktop
        echo.
        echo 请安装 Docker Desktop for Windows:
        echo   https://docs.docker.com/desktop/install/windows-install/
        pause
        exit /b 1
    )
) else (
    echo ✅ Docker daemon 正在运行
)

echo.

:: 如果容器已在运行，先停止
docker ps -q -f "name=%CONTAINER_NAME%" 2>nul | findstr /r "." >nul
if %errorlevel% equ 0 (
    echo ⚠️  容器 %CONTAINER_NAME% 已在运行，正在重启...
    docker stop %CONTAINER_NAME% >nul 2>&1
    docker rm %CONTAINER_NAME% >nul 2>&1
) else (
    docker ps -aq -f "name=%CONTAINER_NAME%" 2>nul | findstr /r "." >nul
    if %errorlevel% equ 0 (
        docker rm %CONTAINER_NAME% >nul 2>&1
    )
)

:: 构建镜像
echo 🔨 正在构建镜像 %IMAGE_NAME% ...
docker build -f scripts/Dockerfile -t %IMAGE_NAME% .
if %errorlevel% neq 0 (
    echo ❌ 镜像构建失败
    pause
    exit /b 1
)

:: 创建报告目录
set REPORTS_DIR=%USERPROFILE%\.ddo_pulse\reports
if not exist "%REPORTS_DIR%" mkdir "%REPORTS_DIR%"

:: 启动容器
echo 🚀 正在启动容器 (宿主机端口: %HOST_PORT%, 容器端口: %API_PORT%) ...
docker run -d ^
    --name %CONTAINER_NAME% ^
    -p %HOST_PORT%:%API_PORT% ^
    -e DDO_PULSE_API_PORT=%API_PORT% ^
    -v ddo-pulse-data:/root/.ddo_pulse ^
    -v "%REPORTS_DIR%:/root/.ddo_pulse/reports" ^
    %IMAGE_NAME%

if %errorlevel% neq 0 (
    echo ❌ 容器启动失败
    pause
    exit /b 1
)

echo.
echo ✅ Ddo-Pulse 已启动
echo.
echo 📌 访问地址: http://localhost:%HOST_PORT%
echo 📊 报告目录: %REPORTS_DIR%
echo 📝 查看日志: docker logs -f %CONTAINER_NAME%
echo.
echo 常用命令:
echo   停止服务: scripts\docker-stop-win.bat
echo   查看日志: docker logs -f %CONTAINER_NAME%
echo   进入容器: docker exec -it %CONTAINER_NAME% /bin/bash
echo.
pause
