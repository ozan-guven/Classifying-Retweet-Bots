import pyautogui as pg
x=271
y=81
print(pg.position())

pg.click(x, y)
pg.typewrite("https://google.com")

pg.hotkey('ctrl', 'c')