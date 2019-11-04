# -*- coding: utf8 -*-
from random import randint
import xlsxwriter
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidgetItem
import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, QTimer
import sqlite3


LEVELS = [("Easy", 8, 10), ("Medium", 16, 40), ("Hard", 24, 99)]
INFOS = ("Flag", "Bomb", "Open", "Close", "Question")


class Cell:
    def __init__(self, info):
        self.info = info
        self.bombs_near = -1
    
    def add_to_info(self, str1):
        '''Adds str1 to info about this cell'''
        self.info.append(str1)
        self.info = list(set(self.info))
    
    def is_bombed(self):
        '''Returns bool value: True if there is a bomb in this cell else: False'''
        return "Bomb" in self.info
    
    def set_bombs_near(self, n):
        '''Sets amount of bombs near this cell'''
        self.bombs_near = n
    
    def get_bombs_near(self):
        '''Returns amount of bombs near this cell'''
        return self.bombs_near
    
    def get_info(self):
        '''Returns tuple of information about this cell'''
        return self.info
    
    def set_info(self, info):
        '''Sets tuple of information about this cell'''
        self.info = info


class Pole:
    def __init__(self, level):
        self.level_name = level[0]
        self.size = level[1]
        self.bombs_amount = level[2]
        self.pole = []
        self.generate_pole()
    
    def generate_pole(self):
        '''Generates pole with bombs'''
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
        '''Sets amount of bombs near all cells of pole'''
        for i in range(self.size):
            for j in range(self.size):
                bombs_amount = 0
                for k in range(-1, 2):
                    for m in range(-1, 2):
                        if (k == 0) and (m == 0):
                            continue
                        x = i + k
                        y = j + m
                        if (x < 0) or (y < 0) or (x >= self.size) or (y >= self.size):
                            continue
                        if self.pole[x][y].is_bombed():
                            bombs_amount += 1
                self.pole[i][j].set_bombs_near(bombs_amount)
    
    def move(self, x, y):
        '''Imitates game move in cell(x, y)
        Returns None if cell is not in pole, False if player is lost, else True'''
        if (x < 0) or (y < 0) or (x >= self.size) or (y >= self.size):
            return None
        if self.pole[x][y].is_bombed():
            return False
        self.open_cells(x, y)
        return True
        
    def open_cells(self, x, y):
        '''Opens all cells for player near cell(x, y) if cell(x, y) has no bombs near itself'''
        info = self.pole[x][y].get_info()
        if "Close" in info:
            del info[info.index("Close")]
        info = []
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
        '''Returns tuple of tuple : game pole'''
        return self.pole
    
    def get_info_cell(self, x, y):
        '''Returns None if cell(x, y) not in pole, else returns info about cell(x, y)'''
        if (x < 0) or (y < 0) or (x >= self.size) or (y >= self.size):
            return None
        return self.pole[x][y].get_info()
    
    def set_info_cell(self, x, y, info):
        '''Returns None if cell(x, y) not in pole, else sets info for cell(x, y)'''
        if (x < 0) or (y < 0) or (x >= self.size) or (y >= self.size):
            return None
        self.pole[x][y].set_info(info)
    
    def get_bombs_near_cell(self, x, y):
        '''Returns None if cell(x, y) not in pole, else returns amount of bombs near cell(x, y)'''
        if (x < 0) or (y < 0) or (x >= self.size) or (y >= self.size):
            return None
        return self.pole[x][y].get_bombs_near()
    
    def check_win(self):
        '''Checks win
        Return True if player wins, else False'''
        for i in self.pole:
            for j in i:
                if (not j.is_bombed()) and ('Open' not in j.get_info()):
                    return False
        return True


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
        self.user_name = ''
        self.last_level = 1
        self.init_start()
    
    def init_start(self):
        '''Initialize start menu of game'''
        self.setMinimumSize(0, 0)
        self.setMaximumSize(2000, 2000)              
        uic.loadUi('designStart.ui', self)
        self.con = sqlite3.connect('games.db')
        self.setMinimumSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())        
        self.game_now = False
        self.line.setText(self.user_name)
        self.play.clicked.connect(self.init_game)
        self.st.clicked.connect(self.statistic)
        self.pole = None
        if self.last_level == 1:
            self.easy.setChecked(True)
        elif self.last_level == 2:
            self.medium.setChecked(True)
        else:
            self.hard.setChecked(True)
    
    def statistic(self):
        '''Initialize start menu of statistic'''
        self.user_name = self.line.text()
        if self.easy.isChecked():
            self.last_level = 1
        elif self.medium.isChecked():
            self.last_level = 2
        else:
            self.last_level = 3
        self.setMinimumSize(0, 0)
        self.setMaximumSize(2000, 2000)              
        uic.loadUi('designStatistic.ui', self)
        self.setMinimumSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())
        self.exit.clicked.connect(self.init_start)
        cur = self.con.cursor()
        self.games = cur.execute('SELECT * FROM games').fetchall()
        self.draw_games()
        self.filter.clicked.connect(self.filtrate)
        self.to_excel.clicked.connect(self.convert_to_excel)
    
    def convert_to_excel(self):
        '''Make Excel file from games'''
        wb = xlsxwriter.Workbook('res.xlsx')
        cur = self.con.cursor()
        sh = wb.add_worksheet()
        sh.write(0, 1, 'Имя')
        sh.write(0, 2, 'Уровень')
        sh.write(0, 3, 'Результат')
        sh.write(0, 4, 'Время')
        for i in range(len(self.games)):
            name = cur.execute('''SELECT name FROM players
            WHERE id = ''' + str(self.games[i][0])).fetchone()[0]
            sh.write(i + 1, 0, i + 1)
            sh.write(i + 1, 1, name)
            d = {1: 'Легкий', 2: 'Средний', 3: 'Сложный'}
            sh.write(i + 1, 2, d[self.games[i][1]])
            d = {1: 'Победа', 0: 'Поражение'}
            sh.write(i + 1, 3, d[self.games[i][2]])
            sh.write(i + 1, 4, self.games[i][3])
        wb.close()
    
    def filtrate(self):
        '''Filtrate games in statistics'''
        cur = self.con.cursor()
        self.games = cur.execute('SELECT * FROM games').fetchall()
        if self.player_name.text() != '':
            self.games = list(filter(lambda x: self.player_name.text() == cur.execute('''
            SELECT name FROM players
            WHERE id = ''' + str(x[0])).fetchone()[0], self.games))
        levels = [1, 2, 3]
        if self.r1.isChecked():
            levels = [1]
        elif self.r2.isChecked():
            levels = [2]
        elif self.r3.isChecked():
            levels = [3]
        self.games = list(filter(lambda x: x[1] in levels, self.games))
        results = [0, 1]
        if self.r4.isChecked():
            results = [1]
        elif self.r5.isChecked():
            results = [0]
        self.games = list(filter(lambda x: x[2] in results, self.games))
        try:
            if self.r6.isChecked():
                self.games = list(filter(lambda x: x[3] > int(self.time_line.text()), self.games))
            elif self.r7.isChecked():
                self.games = list(filter(lambda x: x[3] < int(self.time_line.text()), self.games))
            else:
                self.games = list(filter(lambda x: x[3] == int(self.time_line.text()), self.games))
        except ValueError:
            self.draw_games()
            return
        self.draw_games()
        
    def draw_games(self):
        '''Display table of games on screen'''
        cur = self.con.cursor()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Имя', 'Уровень', 'Результат', 'Время'])
        self.table.setRowCount(len(self.games))
        for i in range(len(self.games)):
            name = cur.execute('''SELECT name FROM players
            WHERE id = ''' + str(self.games[i][0])).fetchone()[0]
            self.table.setItem(i, 0, QTableWidgetItem('  ' + name + '  '))
            d = {1: '  Легкий  ', 2: '  Средний  ', 3: '  Сложный  '}
            self.table.setItem(i, 1, QTableWidgetItem(d[self.games[i][1]]))
            d = {1: '  Победа  ', 0: '  Поражение  '}
            self.table.setItem(i, 2, QTableWidgetItem(d[self.games[i][2]]))
            self.table.setItem(i, 3, QTableWidgetItem(str(self.games[i][3])))
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
    
    def init_game(self):
        '''Initialize game'''
        self.user_name = self.line.text()
        if self.easy.isChecked():
            self.last_level = 1
        elif self.medium.isChecked():
            self.last_level = 2
        else:
            self.last_level = 3        
        self.check_user(self.user_name)
        self.time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(1000)
        self.level = 0
        self.bombs_last = 0
        if self.easy.isChecked():
            self.pole = Pole(LEVELS[0])
            self.size = LEVELS[0][1]
            self.level = 1
            self.bombs_last = LEVELS[0][2]
        elif self.medium.isChecked():
            self.pole = Pole(LEVELS[1])
            self.size = LEVELS[1][1]
            self.level = 2
            self.bombs_last = LEVELS[1][2]
        else:
            self.pole = Pole(LEVELS[2])
            self.size = LEVELS[2][1]
            self.level = 3
            self.bombs_last = LEVELS[2][2]
        self.game_now = True
        uic.loadUi('designGame.ui', self)
        width = 25 * self.size + 40
        height = 25 * self.size + 180
        self.setGeometry(300, 300, width, height)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.pushButton.resize(3 / 4 * self.size * 25, self.pushButton.height())
        self.pushButton.move((width - self.pushButton.width()) / 2,
                             height - self.pushButton.height() - 30)
        self.buttons = []
        self.pushButton.clicked.connect(self.init_start_after_game)
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
        self.time_label.move(width / 2 - 50, 25 * self.size + 25)
        self.bomb_label.move(width / 2 - 80, 25 * self.size + 63)
        self.bomb_label.setText('Осталось бомб: ' + str(self.bombs_last))
    
    def init_start_after_game(self):
        '''Initialize start menu after game'''
        self.timer.stop()
        self.init_start()
    
    def on_timer(self):
        '''Process measuring the time'''
        self.time += 1
        minutes = str(self.time // 60)
        seconds = str(self.time % 60)
        if len(minutes) == 1:
            minutes = '0' + minutes
        if len(seconds) == 1:
            seconds = '0' + seconds
        self.time_label.setText(minutes + ':' + seconds)
    
    def check_user(self, name):
        '''If user name not in database create it'''
        cur = self.con.cursor()
        mass = cur.execute('''SELECT id FROM players
        WHERE name = "''' + name + '"').fetchall()
        if len(mass) == 0:
            cur.execute('INSERT INTO players(name) VALUES("' + name + '")')
            self.con.commit()
    
    def game_click(self, send, but):
        '''Process clicks in game'''
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
                self.bombs_last += 1
                self.bomb_label.setText('Осталось бомб: ' + str(self.bombs_last))
            elif "Question" in info:
                del info[info.index("Question")]
            else:
                if self.bombs_last > 0:
                    info.append("Flag")
                    self.bombs_last -= 1
                    self.bomb_label.setText('Осталось бомб: ' + str(self.bombs_last))
                else:
                    info.append("Question")
            self.pole.set_info_cell(x, y, info)
        else:
            info = self.pole.get_info_cell(x, y)
            if ("Flag" not in info) and ("Question" not in info):
                if not self.pole.move(x, y):
                    self.failed(x, y)
                    return
                if self.pole.check_win():
                    self.win()
                    return
            self.bombs_last = {1: 10, 2: 40, 3: 99}[self.level]
            for i in range(self.size):
                for j in range(self.size):
                    if 'Flag' in self.pole.get_info_cell(i, j):
                        self.bombs_last -= 1
            self.bomb_label.setText('Осталось бомб: ' + str(self.bombs_last))
        self.draw()
    
    def win(self):
        '''Process end of game, when player win'''
        self.game_now = False
        self.timer.stop()
        cur = self.con.cursor()
        p_id = cur.execute('''SELECT id FROM players
        WHERE name = "''' + self.user_name + '"').fetchone()[0]
        cur.execute('INSERT INTO games VALUES(' + str(p_id) +
                    ', ' + str(self.level) + ', 1, ' + str(self.time) + ')')
        self.con.commit()
        self.win_draw()
    
    def win_draw(self):
        '''Draw end pole of game, when player win'''
        self.bomb_label.setText('Вы выиграли')
        width = 25 * self.size + 40
        self.bomb_label.move(width / 2 - 60, 25 * self.size + 63)
        for i in range(self.size):
            for j in range(self.size):
                info = self.pole.get_info_cell(i, j)
                if "Bomb" in info:
                    self.buttons[i][j].setIcon(QIcon("bomb2.jpg"))
                    self.buttons[i][j].setIconSize(QSize(29, 25))
                else:
                    self.buttons[i][j].setIcon(QIcon("0.jpg"))
                    self.buttons[i][j].setEnabled(False)
    
    def failed(self, x, y):
        '''Process end of game, when player lose'''
        self.game_now = False
        self.timer.stop()
        self.end_draw(x, y)
        cur = self.con.cursor()
        p_id = cur.execute('''SELECT id FROM players
        WHERE name = "''' + self.user_name + '"').fetchone()[0]
        cur.execute('INSERT INTO games VALUES(' + str(p_id) + ', ' + 
                    str(self.level) + ', 0, ' + str(self.time) + ')')
        self.con.commit()        
    
    def end_draw(self, x, y):
        '''Draw end pole of game, when player lose'''
        self.bomb_label.setText('Вы проиграли')
        width = 25 * self.size + 40
        self.bomb_label.move(width / 2 - 65, 25 * self.size + 63)
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
        '''Draw pole in game'''
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
                        self.buttons[i][j].setIcon(QIcon("0.jpg"))
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