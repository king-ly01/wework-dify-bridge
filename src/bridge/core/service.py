"""服务管理模块"""

import os
import subprocess
import signal
import sys


def get_main_script() -> str | None:
    """获取主程序路径"""
    this_dir = os.path.dirname(os.path.abspath(__file__))
    # 检查安装后的包路径
    pkg_main = os.path.join(this_dir, "..", "..", "..", "core", "bridge_server.py")
    if os.path.exists(pkg_main):
        return os.path.abspath(pkg_main)
    
    # 检查开发环境路径
    dev_main = os.path.join(this_dir, "..", "..", "core", "bridge_server.py")
    if os.path.exists(dev_main):
        return os.path.abspath(dev_main)
    
    return None


def get_pid(pid_file: str) -> int | None:
    """获取进程 ID"""
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None
    return None


def is_running(pid_file: str) -> tuple[bool, int | None]:
    """检查服务是否运行"""
    pid = get_pid(pid_file)
    if pid:
        try:
            os.kill(pid, 0)
            return True, pid
        except ProcessLookupError:
            return False, None
    return False, None


def reload_config(pid_file: str) -> tuple[bool, str]:
    """发送信号给服务进程重新加载配置"""
    running, pid = is_running(pid_file)
    if not running:
        return False, "服务未运行"
    
    try:
        # 发送 SIGHUP 信号触发配置重载
        os.kill(pid, signal.SIGHUP)
        return True, f"已通知服务重载配置 (PID: {pid})"
    except Exception as e:
        return False, f"发送信号失败: {e}"


def start_service(pid_file: str, log_file: str) -> tuple[bool, str]:
    """启动服务"""
    running, pid = is_running(pid_file)
    if running:
        return False, f"服务已在运行中 (PID: {pid})"
    
    main_script = get_main_script()
    if not main_script:
        return False, "找不到主程序文件"
    
    try:
        # 使用 nohup 启动后台进程
        with open(log_file, 'a') as log:
            proc = subprocess.Popen(
                [sys.executable, main_script],
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            # 保存 PID
            with open(pid_file, 'w') as f:
                f.write(str(proc.pid))
        return True, f"服务已启动 (PID: {proc.pid})"
    except Exception as e:
        return False, f"启动失败: {e}"


def stop_service(pid_file: str) -> tuple[bool, str]:
    """停止服务"""
    running, pid = is_running(pid_file)
    if not running:
        # 清理残留的 pid 文件
        if os.path.exists(pid_file):
            os.remove(pid_file)
        return False, "服务未运行"
    
    try:
        os.kill(pid, signal.SIGTERM)
        # 等待进程结束
        import time
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except ProcessLookupError:
                break
        
        if os.path.exists(pid_file):
            os.remove(pid_file)
        return True, f"服务已停止 (PID: {pid})"
    except Exception as e:
        return False, f"停止失败: {e}"
