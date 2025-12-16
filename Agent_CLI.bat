@echo off
setlocal
pushd "%~dp0"
python -m agent.chat_cli
popd
endlocal

