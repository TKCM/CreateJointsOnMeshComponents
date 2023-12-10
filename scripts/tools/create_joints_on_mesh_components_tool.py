# icon file : https://www.veryicon.com/

###################################################################################################################################
###################################################################################################################################
# モジュール
import os
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import functools

# Mayaモジュール
import maya.api.OpenMaya as om2
import maya.mel as mel
import maya.cmds as cmds

# 自前のモジュール
import tools.tool_base as TKCM_UI
import util.util as TKCM_Util
import importlib
importlib.reload( TKCM_UI )
importlib.reload( TKCM_Util )

###################################################################################################################################
###################################################################################################################################
## カスタムウィジェット

class CustomGroupBox(QtWidgets.QMainWindow):
    def __init__(self, parent: QtWidgets.QWidget = None, flags: QtCore.Qt.WindowFlags = QtCore.Qt.WindowFlags(), title="") -> None:
        super(CustomGroupBox, self).__init__(parent, flags)

        # メンバーインスタンス変数
        self.dir_path = os.path.dirname(__file__)
        self.groupBox = QtWidgets.QGroupBox(self)
        self.groupBox.setObjectName("groupBox")
        self.groupBox.setTitle(title)
        self.layout_ = QtWidgets.QVBoxLayout(self)

        self.groupBox.setLayout(self.layout_)
        self.setCentralWidget(self.groupBox)
        self.setContentsMargins(0, 10, 0, 10)
        self.setStyleSheet("""
            QGroupBox#groupBox  {
                border: 1px solid;
                border-color: #3d3d3d;
                background-color: #3d3d3d;
                margin-top: 15px;
                font-size: 11px;
            }

            QGroupBox::title#groupBox  {
                color: #b8b8b8;
                background-color: #3d3d3d;
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 5px 8000px 5px 8000px;
            }
        """)

class CustomIconButton(QtWidgets.QToolButton):
    def __init__(self):
        super().__init__()

        # メンバーインスタンス変数
        self.icon_path_list = []
        self.icon_id = 0

        # スタイルシートを使用してボタンの枠を非表示にする
        self.setStyleSheet(
            """
            QToolButton {
                border: none;
                padding: 0px;
            }
            QToolButton:hover, QToolButton:checked {
                background-color: transparent;
            }
            """
        )

    def append_icon_path(self, path):
        self.icon_path_list.append(path)
        self.setIcon(QtGui.QIcon(self.icon_path_list[0]))

    def change_icon(self, id):
        if id < len(self.icon_path_list) :
            self.setIcon(QtGui.QIcon(self.icon_path_list[id]))
            self.icon_id = id
    
    def increment_icon(self, loop: bool=True):
        if len(self.icon_path_list) - 1 == self.icon_id:
            self.change_icon(0)
        else:
            self.change_icon(self.icon_id + 1)

class SubWindow(QtWidgets.QWidget):
    def __init__(self, main_window, parent=None):
        super(SubWindow, self).__init__(parent)
        self.setWindowTitle("joint options")

        # メンバーインスタンス変数
        self.parent_window = main_window
        self.joint_orient_0_ = True
        self.axis_type=3
        self.aim_neg=False
        self.up_neg=False

        self.init_ui()
        self.setWindowFlags(QtCore.Qt.Popup)

    def init_ui(self):
        label = QtWidgets.QLabel("-- option --")

        # - ボタン
        self.joint_orient = QtWidgets.QCheckBox("joint orient = 0,0,0", self)
        self.joint_orient.setChecked(self.joint_orient_0_)
        self.joint_orient.clicked.connect(self.fn_joint_orient)

        # - プルダウンメニュー - ボタン - ボタン
        self.joint_axis = QtWidgets.QComboBox()
        self.joint_axis.addItems([\
            "Aim Axis = Z / Up Axis = Y", \
            "Aim Axis = Z / Up Axis = X", \
            "Aim Axis = X / Up Axis = Z", \
            "Aim Axis = X / Up Axis = Y", \
            "Aim Axis = Y / Up Axis = X", \
            "Aim Axis = Y / Up Axis = Z"])
        self.joint_axis.setCurrentIndex(self.axis_type)  # 初期状態を設定
        self.joint_axis.currentIndexChanged.connect(self.fn_joint_axis)  # 選択が変わったときに関数を実行する
        self.joint_aim_neg = QtWidgets.QCheckBox("Aim Axis negative", self)
        self.joint_aim_neg.setChecked(self.aim_neg)
        self.joint_aim_neg.clicked.connect(self.fn_joint_aim_neg)
        self.joint_up_neg = QtWidgets.QCheckBox("Up  Axis negative", self)
        self.joint_up_neg.setChecked(self.up_neg)
        self.joint_up_neg.clicked.connect(self.fn_joint_up_neg)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.joint_orient)
        layout.addWidget(self.joint_axis)
        layout.addWidget(self.joint_aim_neg)
        layout.addWidget(self.joint_up_neg)
    
    def fn_joint_orient(self, index):
        self.joint_orient_0_=index

    def fn_joint_axis(self, index):
        self.axis_type=index
        self.parent_window.debug_draw(True)

    def fn_joint_aim_neg(self, index):
        self.aim_neg=index
        self.parent_window.debug_draw(True)
    
    def fn_joint_up_neg(self, index):
        self.up_neg=index
        self.parent_window.debug_draw(True)
        
    def closeEvent(self, event):
        # サブウィンドウが閉じられたときにメインウィンドウを有効化する
        self.parent_window.setEnabled(True)
        event.accept()

###################################################################################################################################
###################################################################################################################################
## メイン

class createJointsOnCompTool(TKCM_UI.MayaMainWindowBase):
    def __init__(self):
        super(createJointsOnCompTool, self).__init__()

        # インスタンスのメンバ変数をセットする
        self.dir_path = os.path.dirname(__file__)
        self.sub_window = SubWindow(main_window=self)
        self.select_comp_type = TKCM_Util.MeshCompType.kNon

        self.root_=True
        self.tip_=True
        self.count_=1
        self.type_=0
    
    def closeEvent(self, event):
        self.delete_this_context()
        event.accept()

    def abstract_setup_ui(self, widget:QtWidgets.QWidget):
        self.setWindowTitle("Create Joints On Mesh Components Tool -- 20231209")
        self.resize(500, 100)  # 初期サイズの設定

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        ##################################################################################################
        # 一番上の段 - ボタン - ボタン
        top_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(top_layout)

        self.regist_button = QtWidgets.QPushButton(" Regist Mesh Components")
        self.regist_button.clicked.connect(self.regist_mesh_components)
        self.reselect_button = QtWidgets.QPushButton(" re-select")
        self.reselect_button.clicked.connect(self.reselect_mesh_components)
        
        # 左と右のボタンのサイズ調整
        self.regist_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.reselect_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        # ボタンにアイコンを設定
        self.regist_button.setIcon(QtGui.QIcon(self.dir_path + "/icons/regist.png"))
        self.regist_button.setIconSize(QtCore.QSize(20, 20))
        self.reselect_button.setIcon(QtGui.QIcon(self.dir_path + "/icons/reselect.png"))
        self.reselect_button.setIconSize(QtCore.QSize(20, 20))

        top_layout.addWidget(self.regist_button, 3)  # 幅75%
        top_layout.addWidget(self.reselect_button, 1)  # 幅25%

        ##################################################################################################
        # 次の段 - グループ [[ -プルダウンメニュー - ボタン ], [ - チェックボックス - 整数入力ウィジェット - チェックボックス ], [ - ボタン ]]
        custom_group = CustomGroupBox(title="setting")
        main_layout.addWidget(custom_group)

        # - プルダウンメニュー - ボタン 
        combo_menu_layout = QtWidgets.QHBoxLayout()
        custom_group.layout_.addLayout(combo_menu_layout)
        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems(["On Component Center", "Evenly Interval"])
        self.combo_box.currentIndexChanged.connect(self.toggle_comboBox)  # 選択が変わったときに関数を実行する
        
        combo_menu_layout.addWidget(self.combo_box)

        self.joint_option_button = QtWidgets.QPushButton()
        self.joint_option_button.setIcon(QtGui.QIcon(self.dir_path + "/icons/menu.png"))
        self.joint_option_button.setFixedSize(20,20)
        self.joint_option_button.clicked.connect(self.show_sub_window)
        combo_menu_layout.addWidget(self.joint_option_button)
        
        # - チェックボックス - 整数入力ウィジェット - チェックボックス
        checkbox_spinbox_layout = QtWidgets.QHBoxLayout()
        custom_group.layout_.addLayout(checkbox_spinbox_layout)

        self.root_checkbox = QtWidgets.QCheckBox("root joint")
        self.root_checkbox.stateChanged.connect(self.fn_root_checkbox)
        self.tip_checkbox = QtWidgets.QCheckBox("tip joint")
        self.tip_checkbox.stateChanged.connect(self.fn_tip_checkbox)
        self.spin_box_label = QtWidgets.QLabel("division number")
        self.spin_box = QtWidgets.QSpinBox()
        self.spin_box.setRange(1, 100)
        self.spin_box.valueChanged.connect(self.fn_spin_box)

        checkbox_spinbox_layout.addWidget(self.root_checkbox)
        checkbox_spinbox_layout.addWidget(self.spin_box_label)
        checkbox_spinbox_layout.addWidget(self.spin_box)
        checkbox_spinbox_layout.addWidget(self.tip_checkbox, alignment=QtCore.Qt.AlignRight)
        
        ##################################################################################################
        # 次の段 - ボタン
        lounch_bottom_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(lounch_bottom_layout)        

        self.lounch_button = QtWidgets.QPushButton(" Create Joints")
        self.lounch_button.setIcon(QtGui.QIcon(self.dir_path + "/icons/execute.png"))
        self.lounch_button.setIconSize(QtCore.QSize(30, 30))
        self.lounch_button.clicked.connect(self.create_joints)
        lounch_bottom_layout.addWidget(self.lounch_button)

        self.set_neutral()
    
    ###################################################################################################################################
    def toggle_comboBox(self, index):
        self.type_=index
        if index == 0:  # "On Component Center" の場合
            self.spin_box_label.setEnabled(False)
            self.spin_box.setEnabled(False)
        elif index == 1:  # "Evenly Interval" の場合
            self.spin_box_label.setEnabled(True)
            self.spin_box.setEnabled(True)
        self.debug_draw(True)
    
    def show_sub_window(self):
        # メインウィンドウを無効化してサブウィンドウを表示する
        self.setEnabled(False)
        # サブウィンドウをポップアップ表示
        button_pos = self.sender().mapToGlobal(QtCore.QPoint(0, 0))
        self.sub_window.setGeometry(button_pos.x(), button_pos.y() + 30, 200, 100)
        self.sub_window.adjustSize()
        self.sub_window.show()

    def fn_root_checkbox(self, index):
        self.root_=index
        self.debug_draw(True)

    def fn_tip_checkbox(self, index):
        self.tip_=index
        self.debug_draw(True)
    
    def fn_spin_box(self, index):
        self.count_=index
        self.debug_draw(True)

    def set_neutral(self):
        self.select_comp_type = TKCM_Util.MeshCompType.kNon
        self.select_comp_list = None
        self.reselect_button.setEnabled(False)
        self.combo_box.setCurrentIndex(self.type_)  # 初期状態を設定
        self.combo_box.setEnabled(False)
        self.joint_option_button.setEnabled(False)
        self.root_checkbox.setEnabled(False)
        self.root_checkbox.setChecked(self.root_)
        self.tip_checkbox.setEnabled(False)
        self.tip_checkbox.setChecked(self.tip_)
        self.spin_box_label.setEnabled(False)
        self.spin_box.setEnabled(False)
        self.spin_box.setValue(self.count_)
        self.lounch_button.setEnabled(False)
        self.delete_this_context()

    ###################################################################################################################################
    def regist_mesh_components(self):
        selectMesh = cmds.ls(selection=True, long=True, objectsOnly=True, type='mesh')
        if len(selectMesh) == 0:
            cmds.confirmDialog(title="error", message="After selecting components of a single mesh, please press the button.")
            return
        elif len(selectMesh) != 1:
            cmds.confirmDialog(title="error", message="Multiple meshes are not supported.")
            return
        self.select_comp_list = cmds.ls(orderedSelection=True, long=True)
        if len(self.select_comp_list) < 2:
            cmds.confirmDialog(title="error", message="Requires selection of two or more components.")
            return
        self.select_comp_type = TKCM_Util.selectedComponentType(om2.MGlobal.getActiveSelectionList(), 0)

        self.reselect_button.setEnabled(True)
        self.combo_box.setEnabled(True)
        self.root_checkbox.setEnabled(True)
        self.tip_checkbox.setEnabled(True)
        self.lounch_button.setEnabled(True)
        self.joint_option_button.setEnabled(True)
        self.spin_box_label.setEnabled(self.type_==1)
        self.spin_box.setEnabled(self.type_==1)

        self.debug_draw(True)

    def reselect_mesh_components(self):
        try:
            cmds.select(cl=True)
            for comp_path in self.select_comp_list:
                cmds.select(comp_path, tgl=True)
            
        except :
            cmds.confirmDialog(title="error", message="Components registered with the tool not found in this scene.")
            self.set_neutral()
        
    def create_joints(self):
        try:
            self.reselect_mesh_components()
            cmds.createJointsOnMeshComponents(
                setOnJointOrient=(not self.sub_window.joint_orient_0_),\
                createRootjoint=self.root_,\
                createTipJoint=self.tip_,\
                createType=self.type_,\
                createCount=self.count_,\
                axisType = self.sub_window.axis_type,\
                aimAxisNeg = self.sub_window.aim_neg,\
                upAxisNeg = self.sub_window.up_neg)
        except :
            cmds.confirmDialog(title="error", message="Components registered with the tool not found in this scene.")
            self.set_neutral()
    
    def delete_this_context(self):
        # 同種のコンテキストが既に登録済みの場合は削除する
        for ctx in cmds.lsUI(contexts=True):
            if ctx.startswith('CreateJointsOnMeshComponentsDraw'):
                cmds.deleteUI(ctx)
        temp_ctx = cmds.manipMoveContext()
        cmds.setToolTo(temp_ctx)
        # コンポーネント選択モードを継続する
        if self.select_comp_type == TKCM_Util.MeshCompType.kVertex:
            cmds.SelectVertexMask();
        elif self.select_comp_type == TKCM_Util.MeshCompType.kEdge:
            cmds.SelectEdgeMask();
        elif self.select_comp_type == TKCM_Util.MeshCompType.kFace:
            cmds.SelectFacetMask();
    
    def debug_draw(self, joint_draw_:bool):
        if self.select_comp_type == TKCM_Util.MeshCompType.kNon:
            return
        
        self.delete_this_context()
        self.reselect_mesh_components()
        # コンテキストを登録する
        ctx = cmds.CreateJointsOnMeshComponentsDraw(\
            joint_draw=joint_draw_, \
            create_type=self.type_, \
            create_count=self.count_, \
            create_root=self.root_, \
            create_tip=self.tip_,
            axis_type=self.sub_window.axis_type,\
            aim_neg=self.sub_window.aim_neg,\
            up_neg=self.sub_window.up_neg)
        cmds.setToolTo(ctx)
        

###################################################################################################################################
###################################################################################################################################
###################################################################################################################################
###################################################################################################################################
## コール

def run():
    # コンポーネントの選択順にIDリストを取得するためのオプションを有効にする
    if mel.eval("selectPref -query -trackSelectionOrder") == False:
        mel.eval("selectPref -trackSelectionOrder true")
    
    maya_main_window = createJointsOnCompTool.get_maya_window()

    tool_instance = createJointsOnCompTool.get_or_create_instance(False, False)
    tool_instance.run(maya_main_window)
