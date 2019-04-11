import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
import pandas as pd

class KiwoomAPIWdget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.pwindow = parent
        self.qle_text = ''
        # 라벨 생성
        label_market = QLabel('장 선택 ', self)
        #label_market.move(10, 70)

        # 콤보 박스 생성
        self.cbox_market = QComboBox(self)
        #self.cbox_market.setGeometry(100, 70, 150, 32)
        self.cbox_market.setObjectName(("box"))
        self.cbox_market.addItem("장내", userData=0)
        self.cbox_market.addItem("코스닥", userData=10)
        self.cbox_market.addItem("코넥스", userData=50)

        # 버튼 생성
        btn_market = QPushButton('장 리스트 가져오기', self)
        btn_market.setToolTip('0: 장내, 10: 코스닥, 50: 코넥스 등등등 Spec 참조 KiwoomAPI 장 별 종목코드를 가져옴')
        #btn_market.resize(200, 32)
        #btn_market.move(300, 70)
        btn_market.clicked.connect(self.on_click_market)

        hbox = QHBoxLayout()
        hbox.setSpacing(50)
        hbox.addWidget(label_market)
        hbox.addWidget(self.cbox_market)
        hbox.addWidget(btn_market)
        hbox.addStretch(1)

        box_sp = self.UIStockPrice()
        box_sc = self.UISearchStockCode()

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(box_sc)
        vbox.addLayout(box_sp)

        vbox.addStretch(1)

        self.setLayout(vbox)

    def UIStockPrice(self):
        # 라벨 생성
        lb_sp = QLabel('종목 코드 입력 ', self)


        # 콤보 박스 생성
        self.qle_sp = QLineEdit(self)
        self.qle_sp.textChanged[str].connect(self.on_change_qle_sp)

        # 버튼 생성
        btn_sp = QPushButton('주가 가져오기', self)
        btn_sp.setToolTip('해당 종목 코드의 주가를 가져옴')
        btn_sp.clicked.connect(self.on_click_btn_sp)

        hbox = QHBoxLayout()
        hbox.setSpacing(50)
        hbox.addWidget(lb_sp)
        hbox.addWidget(self.qle_sp)
        hbox.addWidget(btn_sp)
        hbox.addStretch(1)
        return hbox

    def UISearchStockCode(self):
        # 라벨 생성
        lb_sc = QLabel('회사명 입력 ', self)


        # 콤보 박스 생성
        self.qle_sc = QLineEdit(self)
        self.qle_sc.textChanged[str].connect(self.on_change_qle_sc)

        # 버튼 생성
        btn_sc = QPushButton('종목 코드 가져오기', self)
        btn_sc.setToolTip('해당 종목 코드를 가져옴, csv 파일이 존재 해야함')
        btn_sc.clicked.connect(self.on_click_btn_sc)

        hbox = QHBoxLayout()
        hbox.setSpacing(50)
        hbox.addWidget(lb_sc)
        hbox.addWidget(self.qle_sc)
        hbox.addWidget(btn_sc)
        hbox.addStretch(1)
        return hbox


    def on_click_market(self):
        print(self.cbox_market.currentText(), ' ',self.cbox_market.currentData())
        # GetCodeListByMarket 으로 종목코드 요청
        result = self.pwindow.kiwoom.dynamicCall('GetCodeListByMarket(QString)', str(self.cbox_market.currentData()))
        code_list = result.split(';')
        data_list = []

        for code in code_list:
            name = self.pwindow.kiwoom.dynamicCall('GetMasterCodeName(QString)', code)
            data_list.append([name, code])

        # 데이터 프레임으로 만들기
        df = pd.DataFrame(data_list, columns=['회사명', '종목코드'])
        print(df.head())

    def on_click_btn_sp(self):
        print(self.qle_text)
        pass

    def on_change_qle_sp(self):
        self.qle_text = self.qle_sp.text()
        pass

    def on_click_btn_sc(self):
        print(self.qle_text)
        pass

    def on_change_qle_sc(self):
        self.qle_text = self.qle_sp.text()
        pass

class KiwoomAPIWindow(QMainWindow):
    def __init__(self, connect=1):
        super().__init__()
        self.title = 'AutoTrader'
        self.left = 50
        self.top = 50
        self.width = 640
        self.height = 480

        self.initUI()


        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        if connect == 1:
            # API 연결
            self.kiwoom.dynamicCall("CommConnect()")

        # API 연결 되었는지를 Status Bar에 출력
        try:
            self.kiwoom.OnEventConnect.connect(self.login_event)
        except:
            self.login_event(-1)
            print('kiwoom API 호출 실패')

        self.kwidget = KiwoomAPIWdget(self)
        self.setCentralWidget(self.kwidget)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)


    def login_event(self, error):
        if error == 0:
            strs = '로그인 성공 Code : ' + str(error)
            self.statusBar().showMessage(strs)
        else:
            strs = '로그인 실패 Code : ' + str(error)
            self.statusBar().showMessage(strs)





if __name__ == "__main__":
    app = QApplication(sys.argv)
    kaWindow = KiwoomAPIWindow()
    kaWindow.show()
    app.exec_()