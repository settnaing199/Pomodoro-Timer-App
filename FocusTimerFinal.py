from PyQt5 import QtWidgets , QtCore
from PyQt5.QtWidgets import QListWidgetItem , QInputDialog, QMessageBox
import tMangmentWidget
import os
import pymysql


class ContLCDClock(QtWidgets.QWidget):

    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = tMangmentWidget.Ui_Form()
        self.ui.setupUi(self)

        #intiatze starting time
        self.ui.lcdNumber.display("25:00")
        self.time = QtCore.QTime(0, 25, 0)
        self.strCurrentTime  = self.time.toString('hh:mm:ss')
        self.timer = QtCore.QTimer()

        self.workorbreak = 'work' #use to swtich between work time and break time

        #intalialize database connection
        self.websites = []
        self.DBConnection()

        #host file in Mac and Linix
        #can access on terminal by typing "sudo nano /etc/hosts" on Linix
        self.host_path = r"/etc/hosts"
        # redirect website back to host address
        self.redirect = "127.0.0.1"


        #button in QtWidgets
        self.ui.startButton.clicked.connect(self.click_start)
        self.ui.addButton.clicked.connect(self.addNewItem)
        self.ui.removeButton.clicked.connect(self.removeItem)
        self.ui.resetButton.clicked.connect(self.resetItem)



    #Database connection
    def DBConnection(self):
        # local host , user, password, database Name
        self.db = pymysql.connect('localhost', 'root', '','test1' )

        # prepare a cursor object using cursor() method
        # use to call SQL queires on python
        self.cursor = self.db.cursor()

        self.sql ="SELECT * FROM website"

        try:
            self.cursor.execute(self.sql)
            #fetch all the data from the database
            self.results = self.cursor.fetchall()
        except:
            print('Error: unable to fetch data')

        self.results = list(self.results)

        # add to list on UI and store in websites list for web blocker
        for i in self.results:
            self.ui.listWidget.addItem(str(i)[2:-3])
            self.websites.append(str(i)[2:-3])



    #Timer Function start
    def click_start(self):
        if(self.workorbreak == 'work'):
            self.websiteBlockOn()

        self.timer.start(1000)
        self.timer.timeout.connect(self.updateTime)

    #call when timer hits 0
    def click_reset(self):
        self.timer.stop()
        if(self.workorbreak == 'work'):
            self.workorbreak = "break"
            self.starttime = 5
            self.ui.label.setText("BREAK TIME")
        else:
            self.workorbreak = "work"
            self.starttime = 25
            self.ui.label.setText("WORK TIME")


        self.ui.lcdNumber.display(str(self.starttime) + ":00")
        self.time = QtCore.QTime(0,self.starttime, 0)
        self.strCurrentTime = self.time.toString('hh:mm:ss')

    def updateTime(self):
        self.time = self.time.addSecs(-1)
        self.strCurrentTime = self.time.toString('hh:mm:ss')
        self.ui.lcdNumber.display(self.strCurrentTime)
        #if current time is equal to 0, stop the time
        if(self.strCurrentTime == '00:00:00'):
            self.click_reset()
            self.websiteBlockOff()
            self.ui.startButton.setEnabled(True)
        else:
            self.ui.startButton.setEnabled(False)
            print("HI")

    def websiteBlockOff(self):
        with open(self.host_path,'r+') as file:
            content = file.readlines();
            file.seek(0)
            for line in content:
                if not any(website in line for website in self.websites):
                    file.write(line)
            file.truncate()


    def websiteBlockOn(self):
        with open(self.host_path,"r+") as fileptr:
            content = fileptr.read()
            for website in self.websites:
                if website in content:
                    pass
                else:
                    fileptr.write(self.redirect+" "+website+"\n")

    #timer FUnction end

    def addNewItem(self):
        text, result = QInputDialog.getText(self, "Add URL", "Enter URL: ")
        if result == True:
            self.ui.listWidget.addItem(text)
            self.websites.append(text)


        self.sql = """INSERT INTO website(url)
        VALUES('%s')""" % (''.join(text))

        try:
            self.cursor.execute(self.sql)
            self.db.commit()

        except:
           # Rollback in case there is any error
           self.db.rollback()



    #Web Blocker Start
    def removeItem(self):
        row = self.ui.listWidget.currentRow()
        item = self.ui.listWidget.item(row)

        if item is None:
            return

        reply = QMessageBox.question(self, 'Remove URL', "You want to remove '{0}'".format(str(item.text())),
                                 QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.websites.remove(str(item.text()))


            self.sql = """DELETE from website WHERE url = '%s'""" % (''.join(str(item.text())))
            try:
                self.cursor.execute(self.sql)
                self.db.commit()
            except:
               # Rollback in case there is any error
               self.db.rollback()

            item = self.ui.listWidget.takeItem(row)
            del item


    def resetItem(self):
            reply = QMessageBox.question(self, 'Reset URL', "Remove All URL?",
                    QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.websites.clear()
                self.ui.listWidget.clear()
                self.sql = """DELETE FROM website"""
                try:
                    self.cursor.execute(self.sql)
                    self.db.commit()
                except:
                    self.db.rollback()

        #Web Blocker End
    def closeEvent(self, event):
            close = QtWidgets.QMessageBox.question(self,
                                         "QUIT",
                                         "Are you sure want to stop process?",
                                         QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if close == QtWidgets.QMessageBox.Yes:
                self.websiteBlockOff()
                event.accept()
            else:
                event.ignore()



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    c = ContLCDClock()
    c.show()
    sys.exit(app.exec_())
