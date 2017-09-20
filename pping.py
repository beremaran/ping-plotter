#!/usr/bin/env python

import os
import sys
import time
import curses
import argparse
import subprocess
import pingparser

__HOST = "8.8.8.8"

BLOCK_CHAR = u"\u2588"
DELAY_IN_MSEC = 1 * 1000

rows, columns = os.popen('stty size', 'r').read().split()
rows, columns = [int(rows), int(columns)]

min_x, max_x = 0, (columns - 1)
min_y, max_y = 2, (rows - 1)

pingHistory = []
pingMax = -999
pingMin = 999

def map(v, in_min, in_max, out_min, out_max):
    return (v - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
def map_y(v):
    global pingMax, min_y, max_y
    return map(v, 0, pingMax, max_y, min_y)
    
def map_x(v):
    global pingHistory, min_x, max_x
    return map(v, 1, len(pingHistory), min_x, max_x)

def get_center_for(_str):
    global columns
    return int((columns - len(_str)) / 2)

def millis():
    return int(round(time.time() * 1000))

def main(stdscr):
    global rows, columns
    global min_x, max_y, min_y, max_y
    global pingHistory, pingMax, pingMin

    title = "== bPingPlotter =="
    
    lastTime = millis()
    print("Waiting for the first ping ...")
    while(1):
        try:
            _ping = subprocess.check_output(
                ['ping', '-c', '1', sys.argv[1]],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
        except subprocess.CalledProcessError:
            continue
            
        _ping = pingparser.parse(_ping)
        
        hostname = _ping['host']
        currentDelay = float(_ping['avgping'])
        pingMax = max(currentDelay, pingMax)
        pingMin = min(currentDelay, pingMin)
        
        pingHistory.append(currentDelay)
        if len(pingHistory) > (max_x - min_x + 1):
            pingHistory = pingHistory[1:]
        
        pingAvg = sum(pingHistory) / len(pingHistory)
    
        currentDelay_str = "{0:.3f} ms.".format(currentDelay)
        averageDelay_str = "Average:\t{0:.3f} ms.".format(pingAvg)
        maxDelay_str = "Max:\t{0:.3f} ms.".format(pingMax)
        minDelay_str = "Min:\t{0:.3f} ms.".format(pingMin)

        columnQuarter = int(columns / 4) + 1

        stdscr.clear()
        
        for i in range(len(pingHistory)):
            _row = int(round(map_y(pingHistory[i])))
            _column = max(0, (columns - len(pingHistory)) + i - 1)
            stdscr.addch(_row, _column, BLOCK_CHAR)
            for r in range(_row, rows):
                stdscr.addch(r, _column, BLOCK_CHAR)
        
        avg_y = int(map_y(pingAvg))
        stdscr.addstr(avg_y, max_x - 10, "- {0:.3f} -".format(pingAvg))
        
        stdscr.addstr(0, 0, "Host: {}".format(hostname))
        stdscr.addstr(0, get_center_for(title), title, curses.A_BOLD)    
        stdscr.addstr(1, 0, "=" * columns)
        stdscr.addstr(int(rows / 2), get_center_for(currentDelay_str), currentDelay_str, curses.A_BOLD)
        stdscr.addstr(rows - 2, 5, averageDelay_str, curses.A_BOLD)
        stdscr.addstr(rows - 3, 5, maxDelay_str, curses.A_BOLD)
        stdscr.addstr(rows - 4, 5, minDelay_str, curses.A_BOLD)
            
        stdscr.refresh()
        if millis() - lastTime < DELAY_IN_MSEC:
            if(DELAY_IN_MSEC - (millis() - lastTime) > 0):
                time.sleep((DELAY_IN_MSEC - (millis() - lastTime)) / 1000.0)
        lastTime = millis()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ping plotter for terminal')
    parser.add_argument('host', type=str, help='Target host')
    parser.add_argument('--t', type=float, help='Ping interval')
    args = parser.parse_args()
    __HOST = args.host
    if args.t is not None:
        DELAY_IN_MSEC = int(args.t * 1000.0)
    curses.wrapper(main)
