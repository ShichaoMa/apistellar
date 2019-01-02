[aliases]
test=pytest

[tool:pytest]
;when run pytest command, add --roodir here will be effective, but
;the printed message of rootdir is only can be changed by command
;line, so never mind!
addopts = --rootdir=${pwd}/tests --cov-report=html:${pwd}/htmlcov --cov-branch --cov=${pwd}/apistellar/ -vv --disable-warnings
usefixtures =
    mock
;`UNIT_TEST_MODE` used to ignore DriverMixin wrapper conn_manager,
;for it is a module of apistellar, to test it, UNIT_TEST_MODE need
;to be false.
env =
    UNIT_TEST_MODE=false