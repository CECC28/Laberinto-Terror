@echo off
echo =========================================
echo   BUILD - Laberinto del Terror
echo =========================================
echo.

echo [1/3] Instalando dependencias...
pip install pygame pyinstaller opencv-python
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo.
echo [2/3] Creando ejecutable...
pyinstaller --onefile --windowed --name "Laberinto_del_Terror" ^
    --icon=NONE ^
    --add-data "settings.py;." ^
    --add-data "entities.py;." ^
    --add-data "level.py;." ^
    --add-data "skills.py;." ^
    main.py

if %errorlevel% neq 0 (
    echo ERROR: Fallo al crear el ejecutable
    pause
    exit /b 1
)

echo.
echo [3/3] Limpiando archivos temporales...
rmdir /s /q build 2>nul
rmdir /s /q __pycache__ 2>nul
del /q *.spec 2>nul

echo.
echo =========================================
echo   BUILD COMPLETADO
echo   Ejecutable: dist\Laberinto_del_Terror.exe
echo =========================================
pause
