import sys, os, json
from functools import partial
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QLabel, QLineEdit, QMessageBox, QRadioButton, QListWidget, QListWidgetItem, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

PDIR = os.path.dirname(sys.executable) if getattr(sys,"frozen",False) else os.path.dirname(os.path.abspath(__file__));PDIR+="/"

DEFAULT_VALUES = {
    "conf.json": {
        "hide_on_launch": False
    },
    "games.json":[] # {"name":str,"cmd":str,"is_exec":bool} # name:name, cmd:command/path, is_exec:whether it's an executable file or just a command
}

# Create LOG
with open(PDIR+"log.txt","w") as f:
    f.write("")

def LOG(error:Exception|str):
    with open(PDIR+"log.txt","a") as f:
        f.write("\n"+str(error))

GAMES=[];CONF={}

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        global CONF,GAMES
        self.setWindowTitle("PyLauncher")
        self.setMinimumSize(800,600)
        
        CONF = self.load_json("conf.json")
        GAMES = self.load_json("games.json")
        
        self.__fd__ = QFileDialog(caption="Choose executable file...")
        self.__fd__.setNameFilter("Executable Files (*.exe)" if sys.platform == "win32" else "Executable Files (*)")
        
        title = QLabel("PyLauncher")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bold_font = title.font()
        bold_font.setBold(True)
        title.setFont(bold_font)
        
        self.games_list = QListWidget()
        self.games_list.addItems([x["name"] for x in GAMES])
        
        btn_launch = QPushButton("Launch")
        btn_add = QPushButton("Add")
        btn_rem = QPushButton("Remove")
        
        btn_launch.clicked.connect(self.run_game)
        btn_add.clicked.connect(self.add_game)
        btn_rem.clicked.connect(self.rem_game)
        
        games_btns_layout = QVBoxLayout()
        games_btns_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        games_btns_layout.addWidget(btn_launch)
        games_btns_layout.addWidget(btn_add)
        games_btns_layout.addWidget(btn_rem)
        
        games_layout = QHBoxLayout()
        games_layout.addWidget(self.games_list)
        games_layout.addLayout(games_btns_layout)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(title)
        main_layout.addLayout(games_layout)
        self.setLayout(main_layout)
        
        self.gp = QWidget()
        self.gp.setWindowFlag(Qt.WindowType.Tool)
        self.gp.setWindowTitle("PyLauncher | Add Game")
        
        self.gp_name = QLineEdit()
        self.gp_name.setPlaceholderText("Name")
        
        self.gp_type_exec = QRadioButton("Executable")
        self.gp_type_cmd = QRadioButton("Command")
        
        self.gp_type_exec.clicked.connect(self.upd_view_gp)
        self.gp_type_exec.setChecked(True)
        
        self.gp_type_cmd.clicked.connect(self.upd_view_gp)
        
        self.gp_exec_inp = QPushButton("Choose Executable")
        self.gp_exec_inp.clicked.connect(self.choose_exec)
        self.gp_exec_inp.hide()
        
        self.gp_cmd_inp = QLineEdit()
        self.gp_cmd_inp.setPlaceholderText("Command")
        self.gp_cmd_inp.hide()
        
        gp_type_layout = QHBoxLayout()
        gp_type_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        gp_type_layout.addWidget(self.gp_type_exec)
        gp_type_layout.addWidget(self.gp_type_cmd)
        
        gp_ok = QPushButton("OK")
        gp_cancel = QPushButton("Cancel")
        
        gp_ok.clicked.connect(self.game_ok)
        gp_cancel.clicked.connect(self.close_gp)
        
        gp_btns = QHBoxLayout()
        gp_btns.addWidget(gp_ok)
        gp_btns.addWidget(gp_cancel)
        
        gp_layout = QVBoxLayout()
        gp_layout.addWidget(self.gp_name)
        gp_layout.addLayout(gp_type_layout)
        gp_layout.addWidget(self.gp_exec_inp)
        gp_layout.addWidget(self.gp_cmd_inp)
        gp_layout.addLayout(gp_btns)
        self.gp.setLayout(gp_layout)
        
        self.upd_view_gp()
    
    def refresh_games(self):
        self.games_list.clear()
        self.games_list.addItems([x["name"] for x in GAMES])
    
    def choose_exec(self):
        x = self.__fd__.getOpenFileName()
        if x and x[0] != "":
            self.gp_exec_inp.setText(f"Choose Executable ({x[0]})")
        else:
            self.gp_exec_inp.setText("Choose Executable")
        
    def upd_view_gp(self):
        x = self.gp_type_exec.isChecked()
        self.gp_exec_inp.setVisible(x)
        self.gp_cmd_inp.setVisible(not x)
   
    def get_dir_from_txt(self,txt:str):
        return txt[txt.find("(")+1:txt.find(")")]
   
    def game_ok(self):
        self.close_gp()
        name = self.gp_name.text()
        ex = self.gp_type_exec.isChecked()
        GAMES.append({
            "name":name,
            "cmd":self.get_dir_from_txt(self.gp_exec_inp.text()) if ex else self.gp_cmd_inp.text(),
            "is_exec":ex
        })
        self.refresh_games()
    
    def run_game(self):
        pass
    
    def add_game(self):
        self.gp_name.clear()
        self.gp_type_exec.setChecked(True)
        self.upd_view_gp()
        self.gp.show()
    
    def rem_game(self):
        for x in self.games_list.selectedItems():
            GAMES.pop(self.games_list.row(x))
            self.games_list.takeItem(self.games_list.row(x))
    
    def close_gp(self):
        self.gp.hide()
    
    def load_json(self,name:str) -> dict|list:
        try:
            if not os.path.exists(PDIR+name):
                with open(PDIR+name,"w") as f:
                    if name in DEFAULT_VALUES:
                        json.dump(DEFAULT_VALUES[name],f)
                    else:f.write("{}")
            with open(PDIR+name,"r") as f:
                return json.load(f)
        except Exception as e:
            LOG(e)
            return DEFAULT_VALUES[name] if name in DEFAULT_VALUES else []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())