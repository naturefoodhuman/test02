@echo off
REM 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
REM 创建时间（北京时间）：2026-08-01 03:50:00

set APP_HOME=%~dp0
set WRAPPER_JAR=%APP_HOME%gradle\wrapper\gradle-wrapper.jar

if exist "%WRAPPER_JAR%" (
  java -jar "%WRAPPER_JAR%" %*
  exit /b %ERRORLEVEL%
)

where gradle >nul 2>nul
if %ERRORLEVEL% == 0 (
  gradle %*
  exit /b %ERRORLEVEL%
)

echo ERROR: gradle command not found and gradle-wrapper.jar is not committed.
echo Install Gradle 8.10+ or run the Unix gradlew bootstrap under macOS/Linux.
exit /b 1
