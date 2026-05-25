@echo off
echo ================================================
echo MySQL密码重置脚本 - 需要管理员权限
echo ================================================
echo.

echo 正在停止MySQL服务...
net stop MySQL80

if %errorlevel% neq 0 (
    echo 停止MySQL服务失败，请确保以管理员身份运行此脚本
    pause
    exit /b 1
)

echo.
echo MySQL服务已停止，正在重置密码...
echo 请勿关闭此窗口，等待显示"SUCCESS"后会自动退出
echo.

"D:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --defaults-file="D:\ProgramData\MySQL\MySQL Server 8.0\my.ini" --init-file="d:\Documents\GitHub\Project_scholarship\mysql-init.sql" --console

echo.
echo 正在启动MySQL服务...
net start MySQL80

echo.
echo ================================================
echo 密码重置完成！新密码为: 123456
echo ================================================
pause