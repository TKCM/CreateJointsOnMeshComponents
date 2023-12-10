###################################################################################################################################
###################################################################################################################################
# モジュール
import os
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance

# Mayaモジュール
import maya.OpenMayaUI as omUI
from maya.app.general import mayaMixin
###################################################################################################################################
###################################################################################################################################

class MayaMainWindowBase(QtWidgets.QWidget, mayaMixin.MayaQWidgetBaseMixin):
    """ツールUIを制作する際の抽象基底クラス
    MayaQWidgetBaseMixinとの競合でabcモジュールの継承が出来ていない
    """
    ######################################################################################################################
    # メンバー関数
    @staticmethod
    def get_maya_window() -> QtWidgets.QWidget:
        """ホスト（これから生成するウィンドウの親）となるMayaのメインウィンドウのポインタを取得する
        """
        maya_main_window_ptr = omUI.MQtUtil.mainWindow();
        return wrapInstance(int(maya_main_window_ptr), QtWidgets.QWidget);
    
    @classmethod
    def get_or_create_instance(cls, multiple_run: bool=True, keep_instance: bool=True):
        """クラスのインスタンスを返す（存在しない場合はインスタンスを新規作成して返す）
        Args:
            multiple_run (bool)): 複数起動を許可する場合はTrue
            keep_instance (bool): multiple_runがTrueの場合のオプション: 既に存在するインスタンスを優先する場合はTrue
        """
        maya_main_window = MayaMainWindowBase.get_maya_window();
        
        if multiple_run: # 複数の起動がOKの場合
            cls._instance = cls();
            return cls._instance; # 新規インスタンスを返す
        else: # 複数の起動がNGの場合
            instances = [child for child in maya_main_window.children() if isinstance(child, QtWidgets.QWidget) and child.metaObject().className() == cls.__name__]; # Maya上に既に存在するクラスインスタンスを検索する
            if len(instances) == 0: # クラスのインスタンスがまだ存在しなかった場合
                cls._instance = cls();
                return cls._instance;
            else: # クラスのインスタンスが既に存在した場合
                if keep_instance: # 既存のインスタンスを継続して使用する
                    return instances[0]; 
                else: # 既存のインスタンスを全て閉じてから新規作成する
                    for instance in instances:
                        instance.close();
                    cls._instance = cls();
                    return cls._instance;

    def __init__(self):
        maya_window = MayaMainWindowBase.get_maya_window()                
        super().__init__()

        # メンバーインスタンス変数
        _instance = None;
        
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)  # ツールウィンドウを常に前面に表示する

    def run(self, parent_window: QtWidgets.QWidget):
        """ツールウィンドウを起動する
        """
        self.setParent(parent_window, QtCore.Qt.Window)
        self.setup_ui()
        self.show()
        self.raise_()
        self.activateWindow()
    
    def setup_ui(self) :
        widget = QtWidgets.QWidget()
        self.abstract_setup_ui(widget)
        return self
    
    def closeEvent(self, _):
        self.abstract_shutdown_ui()

    ######################################################################################################################
    ## 抽象関数
    ## @abstractmethod

    def abstract_setup_ui(self, widget:QtWidgets.QWidget):
        pass

    def abstract_shutdown_ui(self):
        pass

