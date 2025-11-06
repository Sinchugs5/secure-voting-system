@echo off
echo Adding Python to Windows Firewall...
netsh advfirewall firewall add rule name="Python Flask App" dir=in action=allow protocol=TCP localport=5000
netsh advfirewall firewall add rule name="Python Flask App Out" dir=out action=allow protocol=TCP localport=5000
echo Firewall rules added successfully!
pause