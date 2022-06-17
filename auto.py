import pyautogui as pg
import time

x=296; y=608

x1=87; y1=58

counter = 0

while True:
    print(counter)
    counter += 1
    pg.moveTo(x, y)
    pg.click()
    pg.moveTo(x1,y1)
    pg.click()
    time.sleep(10*60)