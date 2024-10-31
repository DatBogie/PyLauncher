import sys, os, json, subprocess, time
from functools import partial
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QLabel, QLineEdit, QMessageBox, QRadioButton, QListWidget, QListWidgetItem, QFrame
from PyQt6.QtCore import Qt, QModelIndex

PDIR = os.path.dirname(sys.executable) if getattr(sys,"frozen",False) else os.path.dirname(os.path.abspath(__file__));PDIR+="/"

DEFAULT_VALUES = {
    "conf.json": {
        "hide_on_launch": False,
        "save_on_close": True
    },
    "games.json":[] # {"name":str,"cmd":str,"is_exec":bool} # name:name, cmd:command/path, is_exec:whether it's an executable file or just a command
}

# Create LOG
if not os.path.exists(PDIR+"log.txt"):
    with open(PDIR+"log.txt","w") as f:
        f.write("")

def LOG(error:Exception|str):
    with open(PDIR+"log.txt","a") as f:
        f.write("\n"+str(error))

LOG(f"\n\n-- START OF FILE ({time.ctime(time.time())}) --\n\n")

GAMES=[];CONF={}

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        global CONF,GAMES
        self.setWindowTitle("PyLauncher")
        self.setMinimumSize(800,600)
        
        CONF = self.load_json("conf.json")
        GAMES = self.load_json("games.json")
        
        self.p = None
        
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
        btn_kill = QPushButton("Kill")
        btn_edit = QPushButton("Edit")
        btn_add = QPushButton("Add")
        btn_cp = QPushButton("Copy")
        btn_rem = QPushButton("Remove")
        btn_ref = QPushButton("Refresh")
        
        btn_launch.clicked.connect(self.run_game)
        btn_kill.clicked.connect(self.kill_current_process)
        btn_edit.clicked.connect(partial(self.add_game,True))
        btn_add.clicked.connect(self.add_game)
        btn_cp.clicked.connect(self.cp_game)
        btn_rem.clicked.connect(self.rem_game)
        btn_ref.clicked.connect(self.refresh_games)
        
        games_btns_layout = QVBoxLayout()
        games_btns_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        games_btns_layout.addWidget(btn_launch)
        games_btns_layout.addWidget(btn_kill)
        games_btns_layout.addWidget(btn_edit)
        games_btns_layout.addWidget(btn_add)
        games_btns_layout.addWidget(btn_cp)
        games_btns_layout.addWidget(btn_rem)
        games_btns_layout.addWidget(btn_ref)
        
        btn_save = QPushButton("Save")
        btn_close = QPushButton("Close")
        
        btn_save.clicked.connect(self.save_games)
        btn_close.clicked.connect(sys.exit)
        
        games_btns_1_layout = QVBoxLayout()
        games_btns_1_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        games_btns_1_layout.addWidget(btn_save)
        games_btns_1_layout.addWidget(btn_close)
        
        games_layout = QHBoxLayout()
        games_layout.addWidget(self.games_list)
        games_btns_layout_layout = QVBoxLayout()
        games_btns_layout_layout.addLayout(games_btns_layout)
        games_btns_layout_layout.addLayout(games_btns_1_layout)
        games_layout.addLayout(games_btns_layout_layout)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(title)
        main_layout.addLayout(games_layout)
        self.setLayout(main_layout)
        
        self.gp = QWidget()
        self.gp.setWindowFlag(Qt.WindowType.SubWindow)
        self.gp.setWindowTitle("PyLauncher | Add Game")
        
        self.gp_name = QLineEdit()
        self.gp_name.setPlaceholderText("Name")
        
        self.gp_edit = False
        
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
        print(GAMES)
    
    def choose_exec(self):
        x = self.__fd__.getOpenFileName(directory=PDIR if self.gp_exec_inp.text() == "" else self.gp_exec_inp.text())
        if x and x[0] != "":
            self.gp_exec_inp.setText("Choose Executable*")
            self.gp_exec_inp.setToolTip(x[0])
        else:
            self.gp_exec_inp.setText("Choose Executable")
            self.gp_exec_inp.setToolTip("")
    
    def upd_view_gp(self):
        x = self.gp_type_exec.isChecked()
        self.gp_exec_inp.setVisible(x)
        self.gp_cmd_inp.setVisible(not x)
   
    def game_ok(self):
        global GAMES
        self.close_gp()
        name = self.gp_name.text()
        ex = self.gp_type_exec.isChecked()
        if not self.gp_edit:
            GAMES.append({
                "name":name,
                "cmd":self.gp_exec_inp.toolTip() if ex else self.gp_cmd_inp.text(),
                "is_exec":ex
            })
        else:
            for i in self.games_list.selectedIndexes():
                if i.row() < len(GAMES):
                    GAMES[i.row()] = {
                        "name":name,
                        "cmd":self.gp_exec_inp.toolTip() if ex else self.gp_cmd_inp.text(),
                        "is_exec":ex
                    }
        self.refresh_games()
    
    def kill_current_process(self):
        LOG(f"Kill process {self.p}...")
        if self.p:
            self.p.kill()
            LOG("Killing...")
            self.p.wait()
            self.p = None
        LOG("Kill finish.")
    
    def run_game(self):
        try:
            for i in self.games_list.selectedIndexes():
                if i.row() < len(GAMES):
                    game = GAMES[i.row()]
                    if self.p: self.p.kill();self.p.wait()
                    self.p = None
                    if game["is_exec"]:
                        # Launch
                        self.p = subprocess.Popen(game["cmd"])
                    else:
                        # Run
                        self.p = subprocess.Popen(game["cmd"].split(" "))
                    if CONF["hide_on_launch"]:
                        self.hide()
                        self.p.wait()
                        self.show()
                else:LOG(IndexError(f"{i.row()} not in GAMES"))
        except Exception as e:
            LOG(e)
    
    def cp_game(self):
        global GAMES
        for i in self.games_list.selectedIndexes():
            if i.row() < len(GAMES):
                game = GAMES[i.row()]
                GAMES.append({
                    "name":game["name"],
                    "cmd":game["cmd"],
                    "is_exec":game["is_exec"]
                })
                self.refresh_games()
                self.games_list.setCurrentRow(len(GAMES)-1)
                self.add_game(True)
    
    def add_game(self,edit_mode:bool=False):
        self.close_gp()
        self.gp_edit = edit_mode
        if not edit_mode:
            self.gp.setWindowTitle("PyLauncher | Add Game")
            self.gp_name.clear()
            self.gp_exec_inp.setText("Choose Executable")
            self.gp_exec_inp.setToolTip("")
            self.gp_cmd_inp.clear()
            self.gp_type_exec.setChecked(True)
        else:
            if len(self.games_list.selectedIndexes()) < 1:LOG("No game selected to edit!");return
            self.gp.setWindowTitle("PyLauncher | Edit Game")
            for i in self.games_list.selectedIndexes():
                if i.row() < len(GAMES):
                    game = GAMES[i.row()]
                    self.gp_name.setText(game["name"])
                    if game["is_exec"]:
                        self.gp_type_exec.setChecked(True)
                        self.gp_exec_inp.setToolTip(game["cmd"])
                    else:
                        self.gp_type_cmd.setChecked(True)
                        self.gp_cmd_inp.setText(game["cmd"])
        self.upd_view_gp()
        w,h = (self.width()//4,self.height()//4)
        self.gp.setFixedSize(w,h)
        self.gp.move(
            self.x()+(self.width()//2) - (w//2),
            self.y()+(self.height()//2) - (h//2)
        )
        self.gp.show()
    
    def rem_game(self):
        global GAMES
        for x in self.games_list.selectedItems():
            GAMES.pop(self.games_list.row(x))
            self.games_list.takeItem(self.games_list.row(x))
    
    def close_gp(self):
        self.gp.hide()
    
    def save_games(self):
        if self.write_json("games.json",GAMES):
            QMessageBox.information(self,"PyLauncher | Save Games","Saved Succesfully!")
        else:
            QMessageBox.critical(self,"PyLauncher | Save Games","Save Failed!\nCheck log.txt for more details.")
    
    def write_json(self,name:str,data:dict|list) -> bool:
        try:
            with open(PDIR+name,"w") as f:
                json.dump(data,f)
            return True
        except Exception as e:LOG(e);return False
    
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
            try:
                with open(PDIR+name,"w") as f:
                    json.dump(DEFAULT_VALUES[name],f)
            except Exception as e:LOG(e)
            return DEFAULT_VALUES[name] if name in DEFAULT_VALUES else []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())