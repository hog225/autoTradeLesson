import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
import pandas as pd
import globalData as gd
import globalFunc as gf
import os

COM_DATE = "20190516" # 기준일자 600 거래일 전일 부터 현제까지 받아옴

class KiwoomAPIWdget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        self.pwindow = parent

        # 라벨 생성
        label_market = QLabel('장 선택 ', self)
        #label_market.move(10, 70)

        # 콤보 박스 생성
        self.cbox_market = QComboBox(self)
        #self.cbox_market.setGeometry(100, 70, 150, 32)
        self.cbox_market.setObjectName(("box"))
        self.cbox_market.addItem(gd.KOSPI, userData=0)
        self.cbox_market.addItem(gd.KOSDAQ, userData=10)
        self.cbox_market.addItem(gd.KONEX, userData=50)

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

        # UI Set Box 선언
        box_sp = self.UIStockPrice()
        box_sc = self.UISearchStockCode()
        box_rw = self.UIResultWindow()

        # UI Set Box 배치
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(box_sc)
        vbox.addLayout(box_sp)
        vbox.addLayout(box_rw)

        vbox.addStretch(1)

        self.setLayout(vbox)



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

    def UIResultWindow(self):
        lb_rw = QLabel('결과', self)

        # Text 박스 생성
        self.qte_rw = QTextEdit(self)
        self.qte_rw.setReadOnly(True)

        vbox = QVBoxLayout()
        vbox.addWidget(lb_rw)
        vbox.addWidget(self.qte_rw)
        return vbox


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
        df = pd.DataFrame(data_list, columns=[gd.COM_NAME, gd.COM_CODE])

        fileName = self.cbox_market.currentText() + '.csv'
        df.to_csv(fileName)
        try:
            filePath = os.path.dirname(os.path.realpath(fileName))
            prtStr = "종목코드 받아오기 성공\n"
            prtStr += "종목코드 위치 : " + str(filePath) + '\n'
            prtStr += str(df.head())
            print(prtStr)
            self.qte_rw.setText(prtStr)
        except:
            self.qte_rw.setText("종목코드 받아오기 실패")

    def on_click_btn_sp(self):
        # self.pwindow.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", self.qle_sp.text())
        # self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10001_req", "opt10001", 0, "0101")
        # pass
        # 파라미터 세팅
        print(self.qle_sp.text())
        self.pwindow.kiwoom.SetInputValue("종목코드", str(self.qle_sp.text().strip()))
        self.pwindow.kiwoom.SetInputValue("기준일자", COM_DATE)
        self.pwindow.kiwoom.SetInputValue("수정주가구분", "0")
        # sRQName, sTrCode, nPrevNext, sScreenNo

        res = self.pwindow.kiwoom.CommRqData("opt10081_주가조회", "opt10081", 0, "10081")
        if res == 0:
            print('주가 요청 성공!!!!!!' + str(res))
        else:
            print('주가 요청 실패 !!!!!!' + str(res))

        print('api return False ')


    def on_change_qle_sp(self):
        pass

    def on_change_qle_sc(self):
        pass

    def on_click_btn_sc(self):
        fileName = self.cbox_market.currentText() + '.csv'
        res = gf.findFileOndir(fileName)
        if res:
            dfStockDatas = pd.read_csv(fileName)
            try:
                idx = dfStockDatas[gd.COM_NAME].tolist().index(self.qle_sc.text())
                self.qte_rw.setText(str(self.qle_sc.text() + " 존재 !!"))
                # 종목 코드 입력란에 쓰기
                self.qle_sp.setText(str(dfStockDatas[gd.COM_CODE][idx]))

            except Exception as e:
                print (e)
                self.qte_rw.setText(str(self.qle_sc.text() + ' ' +fileName + " 안에서 존재하지 않음"))


        else:
            self.qte_rw.setText(str(fileName + " 존재하지 않음"))

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
            self.kiwoom.OnReceiveTrData.connect(self.receive_trdata)
        except Exception as e:
            self.login_event(-1)
            print('kiwoom API 호출 실패', str(e))


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

    # CallBack 함수
    def receive_trdata(self, sScrNo, sRQName, sTrCode, sRecordName, sPreNext, nDataLength, sErrorCode, sMessage, sSplmMsg):

        if sRQName == "opt10081_주가조회":
            dataCount = self.kiwoom.GetRepeatCnt(sTrCode, sRQName)
            print('총 데이터 수 : ', dataCount)
            code = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "종목코드")
            print("종목코드: " + code)
            print("------------------------------")
            # 가장최근에서 10 거래일 전까지 데이터 조회
            for dataIdx in range(0, 10):
                inputVal = ["일자", "거래량", "시가", "고가", "저가", "현재가"]
                outputVal = ['', '', '', '', '', '']
                for idx, j in enumerate(inputVal):
                    outputVal[idx] = self.kiwoom.GetCommData(sTrCode, sRQName, dataIdx, j)

                for idx, output in enumerate(outputVal):
                    print(inputVal[idx] + output)
                print('----------------')
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kaWindow = KiwoomAPIWindow(1)
    kaWindow.show()
    app.exec_()