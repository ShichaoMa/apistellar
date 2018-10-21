[aliases]
test=pytest

[tool:pytest]
;add --roodir here will be effective, but when run pytest command
;the printed message of rootdir is only can be changed by command
;line, so never mind!
addopts = --rootdir=${pwd}/tests --cov-report=html:${pwd}/htmlcov --cov-branch --cov=${pwd}/apistellar/ -vv --disable-warnings
usefixtures =
    mock
