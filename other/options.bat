@echo off
SETLOCAL EnableDelayedExpansion
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do     rem"') do (
  set "DEL=%%a"
)

set "FRAS_SERVER_PATH=%CD%\RecogServer"
set "INTEL_OPENVINO_DIR=%FRAS_SERVER_PATH%\openvino\runtime\inference_engine"
set "INTEL_DLL_PATH=%CD%\RecogServer\compiler"
set "PATH=%INTEL_OPENVINO_DIR%\bin\Release;%INTEL_DLL_PATH%;%PATH%"
goto :init

:usage
    echo USAGE:
    echo run.bat - an helper script for running FACIAL RECOGNITION BASED ATTENDANCE SYSTEM (w TEMPERATURE).
    echo w/o any argument it will start the FRAS.
    echo This script is a wrapper for the following command group.
    echo %__BAT_NAME% [flags] "optional arguments"
    echo.
    echo. /?, -?, --help	show this help
    echo. ,/r, -r, --run_fras   Run FRAS with default argument.
    echo. /d, -d, --db		Create database.
    echo. /c, -c, --cert	Create db certificate.
    echo. /b, -b, --bulk        Upload data from file.
    goto :eof

:init
    set "__BAT_NAME=%~nx0"

:parse
    if "%~1"==""               call :run_fras & goto :end

    if /i "%~1"=="/?"          call :usage & goto :end
    if /i "%~1"=="-?"          call :usage & goto :end
    if /i "%~1"=="--help"      call :usage & goto :end

    if /i "%~1"=="/r"          call :run_fras & goto :end
    if /i "%~1"=="-r"          call :run_fras & goto :end
    if /i "%~1"=="--run_fras"  call :run_fras & goto :end

    if /i "%~1"=="/d"          call :db & goto :end
    if /i "%~1"=="-d"          call :db & goto :end
    if /i "%~1"=="--db"        call :db & goto :end

    if /i "%~1"=="/c"          call :cert & goto :end
    if /i "%~1"=="-c"          call :cert & goto :end
    if /i "%~1"=="--cert"      call :cert & goto :end

    if /i "%~1"=="/b"          call :bulk & goto :end
    if /i "%~1"=="-b"          call :bulk & goto :end
    if /i "%~1"=="--bulk"      call :bulk & goto :end

    shift
    goto :parse

:run_fras
    call :get_t_fd
    call :get_t_id
    call :get_exp_r_fd
    FRAS.exe --run_fras -t_fd %t_fd% -t_id %t_id% -exp_r_fd %exp_r_fd%
    goto :eof

:get_t_fd
    call :colorEcho 0e "Enter t_fd -"
    set /p "t_fd="
    goto :eof

:get_t_id
    call :colorEcho 0e "Enter t_id -"
    set /p "t_id="
    goto :eof

:get_exp_r_fd
    call :colorEcho 0e "Enter exp_r_fd -"
    set /p "exp_r_fd="
    goto :eof


:::::::::::::::::::::::::::::::::::::: Functions for Bulk Upload :::::::::::::::::::::::::

:set_file_path
    set /p "file_path="
    if exist %file_path% (
        if exist %file_path%\ (
            call :colorEcho 74 "Specified Path is a folder. Please enter path to a file."
            echo.
            goto :set_file_path
        )
        goto :eof
    ) else (
        call :colorEcho 74 "Specified file doesnot exists. Please enter again."
        echo.
        goto :set_file_path
    )

:get_file_path
    call :colorEcho 0e "Enter File Containing Information"
    echo.
    call :colorEcho 47 "Make sure to create a mapping of this file in config.ini"
    echo.
    call :set_file_path
    goto :eof

:set_folder_path
    set /p "folder_path="
    if exist %folder_path%\ (
        goto :eof
    ) else (
        call :colorEcho 74 "Specified Folder doesnot exists. Please enter again."
        echo.
        goto :set_folder_path
    )

:get_folder_name
    call :colorEcho 0e "Enter path to folder containing pics."
    echo.
    call :set_folder_path
    goto :eof

:get_log_file_location
    call :colorEcho 0e "Enter log file path (Press enter to use default location from config.ini)"
    echo.
    set /p "log_file_path="
    goto :eof

:bulk
    call :get_file_path
    call :get_folder_name
    call :get_log_file_location
    echo.
    echo "Provided file path: %file_path%"
    echo.
    echo "Provided Pictures path: %folder_path%"
    echo.

    if "%log_file_path%" == "" (
        echo. "Using default log file path".
        echo.
        FRAS.exe --bulk_upload --person_information_file_path %file_path% --picture_folder %folder_path%
    ) else (
        echo. "Provided log file path: %log_file_path%"
        echo.
        FRAS.exe --bulk_upload --person_information_file_path %file_path% --picture_folder %folder_path% --log_folder %log_file_path%
    )

    goto :eof

:::::::::::::::::::::::::::::::::::::: Functions for creating DB :::::::::::::::::::::::::

:db
    call :get_ip
    call :get_port
    call :get_cert_file
    call :get_sql_file
    FRAS.exe --create_db --ip %db_ip% --port %db_port% --certfile %db_certfile% --sqlfile %db_sqlfile%
    goto :eof

:get_ip
    call :colorEcho 0e "Enter DB IP -"
    set /p "db_ip="
    goto :eof

:get_port
    call :colorEcho 0e "Enter DB Port -"
    set /p "db_port="
    goto :eof

:get_cert_file
    call :colorEcho 0e "Enter certificate file name (default dbinfo.cert) -"
    set /p "db_certfile="
    if "%db_certfile%" == "" (
        set db_certfile=dbinfo.cert
    )
    goto :eof

:get_sql_file
    call :colorEcho 0e "Enter sql file name (default db.sql) -"
    set /p "db_sqlfile="
    if "%db_sqlfile%" == "" (
        set db_sqlfile=db.sql
    )
    goto :eof

::::::::::::::::::::::::::::::::::::::: Functions for certificate :::::::::::::::::::::::::
:cert
    call :user_loop
    call :user_pass
    call :cert_fname
    FRAS.exe --db_cert --username %user% --password %pass% --filename %fname% --write
    set user=
    set pass=
    set fname=
    goto :eof

:user_loop
    call :colorEcho 0e "Enter DB Username -"
    set /p "user="
    echo.
    if "%user%" == "" (
        call :colorEcho 47 "You must enter a username"
        echo.
        Timeout /T 2 /NoBreak>nul
        goto :user_loop
    ) else (
        goto :eof
    )

:user_pass
    powershell -Command $pword = read-host "Enter DB password" -AsSecureString ; ^
                        $BSTR=[System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pword) ; ^
                        [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR) > .tmp.txt 
    set /p pass=<.tmp.txt & del .tmp.txt
    goto :eof

:cert_fname
    call :colorEcho 0e "Enter output certfile name (default name dbinfo.cert)-"
    set /p "fname="
    if "%fname%" == "" (
        set fname=dbinfo.cert
    )
    goto :eof

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:colorEcho
    <nul set /p ".=%DEL%" > "%~2"
    findstr /v /a:%1 /R "^$" "%~2" nul
    del "%~2" > nul 2>&1i
    goto :eof

:end
    exit /B