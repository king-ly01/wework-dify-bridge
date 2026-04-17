@echo off
chcp 65001 >nul
:: wework-dify-bridge Windows 服务管理脚本
:: 用法：双击运行，或在命令行：start.bat [start|stop|restart|status|log]

set SCRIPT_DIR=%~dp0
set MAIN=%SCRIPT_DIR%wework_smart_bot_final.py
set LOG=%SCRIPT_DIR%bridge.log
set PID_FILE=%SCRIPT_DIR%bridge.pid
set SERVICE_NAME=wework-dify-bridge

:: 获取参数，默认为 start
set ACTION=%1
if "%ACTION%"=="" set ACTION=start

if "%ACTION%"=="start"   goto :do_start
if "%ACTION%"=="stop"    goto :do_stop
if "%ACTION%"=="restart" goto :do_restart
if "%ACTION%"=="status"  goto :do_status
if "%ACTION%"=="log"     goto :do_log
if "%ACTION%"=="install" goto :do_install

echo 用法：start.bat [start^|stop^|restart^|status^|log^|install]
echo.
echo   start    启动服务
echo   stop     停止服务
echo   restart  重启服务
echo   status   查看运行状态
echo   log      查看最近日志
echo   install  安装依赖
goto :eof

:: ── 安装依赖 ─────────────────────────────────
:do_install
echo [1/2] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  错误：未找到 Python，请先安装 Python 3.8+
    echo  下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.
echo [2/2] 安装依赖...
python -m pip install -r "%SCRIPT_DIR%requirements.txt"
if errorlevel 1 (
    echo  安装失败，请检查网络或手动执行：
    echo  pip install wecom-aibot-sdk-python aiohttp
    pause
    exit /b 1
)
echo.
echo  依赖安装完成！
echo.
if not exist "%SCRIPT_DIR%config.json" (
    copy "%SCRIPT_DIR%config.example.json" "%SCRIPT_DIR%config.json" >nul
    echo  已生成 config.json，请用记事本填写配置：
    echo  notepad "%SCRIPT_DIR%config.json"
) else (
    echo  config.json 已存在，无需重新生成
)
echo.
echo  下一步：编辑 config.json 后运行 start.bat start
pause
goto :eof

:: ── 启动服务 ─────────────────────────────────
:do_start
tasklist /fi "imagename eq python.exe" /fi "windowtitle eq %SERVICE_NAME%*" 2>nul | find /i "python.exe" >nul
if not errorlevel 1 (
    echo  服务可能已在运行，请先执行 start.bat stop
    goto :eof
)
if not exist "%SCRIPT_DIR%config.json" (
    echo  错误：config.json 不存在，请先运行：start.bat install
    pause
    goto :eof
)
echo  正在启动桥接服务...
start /b "wework-dify-bridge" python "%MAIN%" >> "%LOG%" 2>&1
timeout /t 2 /nobreak >nul
echo  启动成功！日志：%LOG%
echo  查看日志：start.bat log
goto :eof

:: ── 停止服务 ─────────────────────────────────
:do_stop
echo  正在停止服务...
taskkill /fi "windowtitle eq wework-dify-bridge*" /f >nul 2>&1
taskkill /f /im python.exe /fi "windowtitle eq wework-dify-bridge*" >nul 2>&1
echo  服务已停止
goto :eof

:: ── 重启 ─────────────────────────────────────
:do_restart
call :do_stop
timeout /t 2 /nobreak >nul
call :do_start
goto :eof

:: ── 查看状态 ─────────────────────────────────
:do_status
tasklist /fi "imagename eq python.exe" 2>nul | find /i "python.exe" >nul
if errorlevel 1 (
    echo  服务未运行
) else (
    echo  Python 进程运行中（包含本服务）
    echo  日志文件：%LOG%
)
goto :eof

:: ── 查看日志 ─────────────────────────────────
:do_log
if not exist "%LOG%" (
    echo  日志文件不存在
    goto :eof
)
echo  最近 20 条日志：
echo  ----------------------------------------
powershell -command "Get-Content '%LOG%' -Tail 20"
goto :eof
