@echo off


echo "Create DB certificate???(Y or N, Default is N)="
set /p "create_certificate="
if "%create_certificate%" == "Y" (
    echo "Creating Database Certificate."
    echo.
    call options.bat --cert
)

echo "Setup DB????(Y or N, Default is N)="
set /p "setup_db="
if "%setup_db%" == "Y" (
    echo "Setting up DB (This will not setup the database for recognition server. Please setup this information in config.ini before running the recognition.)".
    echo.
    call options.bat --db
)
