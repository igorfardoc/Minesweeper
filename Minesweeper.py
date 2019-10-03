# -*- coding: utf8 -*-
from random import randint
from PyQt5 import uic, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QRadioButton
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtCore import QRect
import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *


LEVELS = [("Easy", 8, 10), ("Medium", 16, 40), ("Hard", 24, 99)]
INFOS = ("Flag", "Bomb", "Open", "Close", "Question")


class Cell:
    def __init__(self, info):
        self.info = info
        self.bombs_near = -1
    
    def add_to_info(self, str1):
        self.info.append(str1)
        self.info = list(set(self.info))
    
    def is_bombed(self):
        return "Bomb" in self.info
    
    def set_bombs_near(self, n):
        self.bombs_near = n
    
    def get_bombs_near(self):
        return self.bombs_near
    
    def get_info(self):
        return self.info
    
    def set_info(self, info):
        self.info = info


class Pole:
    def __init__(self, level):
        self.level_name = level[0]
        self.size = level[1]
        self.bombs_amount = level[2]
        self.pole = []
        self.generate_pole()
    
    def generate_pole(self):
        self.pole = []
        for i in range(self.size):
            self.pole.append([])
            for j in range(self.size):
                self.pole[-1].append(Cell(["Close"]))
        for i in range(self.bombs_amount):
            x = randint(0, self.size - 1)
            y = randint(0, self.size - 1)
            while self.pole[x][y].is_bombed():
                x = randint(0, self.size - 1)
                y = randint(0, self.size - 1)
            self.pole[x][y].add_to_info("Bomb")
        self.set_bombs_near()
    
    def set_bombs_near(self):
        for i in range(self.size):
            for j in range(self.size):
                bombs_amount = 0
                for k in range(-1, 2):
                    for l in range(-1, 2):
                        if (k == 0) and (l == 0):
                            continue
                        x = i + k
                        y = j + l
                        if (x < 0) or (y < 0) or (x >= self.size) or (y >= self.size):
                            continue
                        if self.pole[x][y].is_bombed():
                            bombs_amount += 1
                self.pole[i][j].set_bombs_near(bombs_amount)
    
    def move(self, x, y):
        if (x < 0) or (y < 0) or (x >= self.size) or (y >= self.size):
            return None
        if self.pole[x][y].is_bombed():
            return False
        self.open_cells(x, y)
        return True
        
    def open_cells(self, x, y):
        info = self.pole[x][y].get_info()
        if "Close" in info:
            del info[info.index("Close")]
        self.pole[x][y].set_info(info)
        self.pole[x][y].add_to_info("Open")
        if self.pole[x][y].get_bombs_near() == 0:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if (i == 0) and (j == 0):
                        continue
                    x1 = i + x
                    y1 = j + y
                    if (x1 < 0) or (y1 < 0) or (x1 >= self.size) or (y1 >= self.size):
                        continue
                    if "Close" in self.pole[x1][y1].get_info():
                        self.open_cells(x1, y1)
    
    def get_pole(self):
        return self.pole
    
    def get_info_cell(self, x, y):
        if (x < 0) or (y < 0) or (x >= self.size) or (y >= self.size):
            return None
        return self.pole[x][y].get_info()
    
    def set_info_cell(self, x, y, info):
        if (x < 0) or (y < 0) or (x >= self.size) or (y >= self.size):
            return None
        self.pole[x][y].set_info(info)
    
    def get_bombs_near_cell(self, x, y):
        if (x < 0) or (y < 0) or (x >= self.size) or (y >= self.size):
            return None
        return self.pole[x][y].get_bombs_near()


class PushButtonRight(QPushButton):
    def __init__(self, *args):
        super().__init__(*args)
        self.args = args

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.args[1].game_click(self, "l")
        elif event.button() == Qt.RightButton:
            self.args[1].game_click(self, "r")


class Game(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_start()
    
    def init_start(self):
        self.setMinimumSize(0, 0)
        self.setMaximumSize(2000, 2000)              
        uic.loadUi('designStart.ui', self)
        self.setMinimumSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())        
        self.game_now = False
        self.play.clicked.connect(self.init_game)
        self.pole = None
    
    def init_game(self):
        if self.easy.isChecked():
            self.pole = Pole(LEVELS[0])
            self.size = LEVELS[0][1]
        elif self.medium.isChecked():
            self.pole = Pole(LEVELS[1])
            self.size = LEVELS[1][1]
        else:
            self.pole = Pole(LEVELS[2])
            self.size = LEVELS[2][1]
        self.game_now = True
        uic.loadUi('designGame.ui', self)
        width = 25 * self.size + 40
        height = 25 * self.size + 240
        self.setGeometry(300, 300, width, height)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.pushButton.resize(3 / 4 * self.size * 25, self.pushButton.height())
        self.pushButton.move((width - self.pushButton.width()) / 2,
                             height - self.pushButton.height() - 30)
        self.buttons = []
        self.pushButton.clicked.connect(self.init_start)
        self.grid.setColumnStretch(self.size, self.size)
        self.grid.setRowStretch(self.size, self.size)
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)
        for i in range(self.size):
            self.buttons.append([])
            for j in range(self.size):
                self.buttons[-1].append(PushButtonRight(' ', self))
                self.buttons[i][j].setIcon(QIcon("cell.jpg"))
                self.buttons[i][j].setIconSize(QSize(29, 25))                   
                self.buttons[i][j].resize(25, 25)
                self.buttons[i][j].setMinimumSize(25, 25)
                self.buttons[i][j].setMaximumSize(25, 25)
                self.grid.addWidget(self.buttons[i][j], j, i)
    
    def game_click(self, send, but):
        if not self.game_now:
            return
        x = 0
        y = 0
        for i in range(self.size):
            for j in range(self.size):
                if self.buttons[i][j] == send:
                    x = i
                    y = j
                    break
        if but == "r":
            info = self.pole.get_info_cell(x, y)
            if "Flag" in info:
                del info[info.index("Flag")]
                info.append("Question")
            elif "Question" in info:
                del info[info.index("Question")]
            else:
                info.append("Flag")
            self.pole.set_info_cell(x, y, info)
        else:
            info = self.pole.get_info_cell(x, y)
            if ("Flag" not in info) and ("Question" not in info):
                if not self.pole.move(x, y):
                    self.failed(x, y)
                    return
        self.draw()
    
    def failed(self, x, y):
        self.game_now = False
        self.end_draw(x, y)
    
    def end_draw(self, x, y):
        for i in range(self.size):
            for j in range(self.size):
                info = self.pole.get_info_cell(i, j)
                if (i == x) and (j == y):
                    self.buttons[i][j].setIcon(QIcon("bomb1.jpg"))
                    self.buttons[i][j].setIconSize(QSize(29, 25))
                    continue
                if "Bomb" in info:
                    self.buttons[i][j].setIcon(QIcon("bomb.jpg"))
                    self.buttons[i][j].setIconSize(QSize(29, 25))                    
    
    def draw(self):
        for i in range(self.size):
            for j in range(self.size):
                info = self.pole.get_info_cell(i, j)
                if "Close" in info:
                    if "Flag" in info:
                        self.buttons[i][j].setIcon(QIcon("flag.jpg"))
                        self.buttons[i][j].setIconSize(QSize(29, 25))
                    elif "Question" in info:
                        self.buttons[i][j].setIcon(QIcon("question.jpg"))
                        self.buttons[i][j].setIconSize(QSize(29, 25))
                    else:
                        self.buttons[i][j].setIcon(QIcon("cell.jpg"))
                        self.buttons[i][j].setIconSize(QSize(29, 25))                         
                else:
                    if self.pole.get_bombs_near_cell(i, j) == 0:
                        self.buttons[i][j].setIcon(QIcon())
                    elif self.pole.get_bombs_near_cell(i, j) == 1:
                        self.buttons[i][j].setIcon(QIcon("1.jpg"))
                        self.buttons[i][j].setIconSize(QSize(29, 25)) 
                    elif self.pole.get_bombs_near_cell(i, j) == 2:
                        self.buttons[i][j].setIcon(QIcon("2.jpg"))
                        self.buttons[i][j].setIconSize(QSize(29, 25))
                    elif self.pole.get_bombs_near_cell(i, j) == 3:
                        self.buttons[i][j].setIcon(QIcon("3.jpg"))
                        self.buttons[i][j].setIconSize(QSize(29, 25))
                    elif self.pole.get_bombs_near_cell(i, j) == 4:
                        self.buttons[i][j].setIcon(QIcon("4.jpg"))
                        self.buttons[i][j].setIconSize(QSize(29, 25))   
                    elif self.pole.get_bombs_near_cell(i, j) == 5:
                        self.buttons[i][j].setIcon(QIcon("5.jpg"))
                        self.buttons[i][j].setIconSize(QSize(29, 25))
                    else:
                        self.buttons[i][j].setIcon(QIcon("6.jpg"))
                        self.buttons[i][j].setIconSize(QSize(29, 25))                        
                    self.buttons[i][j].setEnabled(False)
        

app = QApplication(sys.argv)
ex = Game()
ex.show()
sys.exit(app.exec_())