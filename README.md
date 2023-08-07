# Grand Perspective for Yandex Disk

[GrandPerspective](http://grandperspectiv.sourceforge.net/) is MacOS application that shows disk usage.

`gp4yd` is a snippet for collecting file info from Yandex Disk cloud storage 
and prepare input file for Grand Perspective visualisation.

![Screenshot of GrandPerspective report window](sample.png?raw=true "GrandPerspective")

# How to use

- install `requests` modules for Python3
- obtain token with read access for Yandex Cloud and save it to file (details are below), e.g. `my.token`
- call script
```
python3 gp4yd.py -t my.token report.gpscan 
```
- open Grand Perspective App
- import `report.gpscan` via `File | Load Scan Data...` menu 
- enjoy the report

## Token acquisition process
Guide in Russian: https://ypermitin.github.io/devoooops/2022/04/04/%D0%9E%D1%82%D0%BF%D1%80%D0%B0%D0%B2%D0%BA%D0%B0-%D1%84%D0%B0%D0%B9%D0%BB%D0%BE%D0%B2-%D0%B2-Yandex-Disk-%D1%87%D0%B5%D1%80%D0%B5%D0%B7-REST-API-%D0%B8%D0%B7-Bash.html

# See also
gpscan - a utility to create GrandPerspective scan files on other operating systems.

https://github.com/robhaswell/grandperspective-scan

