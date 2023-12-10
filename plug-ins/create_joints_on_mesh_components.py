from __future__ import division

# Mayaモジュール
import maya.mel as mel
import maya.api.OpenMaya as om2
import maya.api.OpenMayaUI as omUI
import maya.api.OpenMayaRender as omR

# 自前のモジュール
import util.util as TKCM_Util
import importlib
importlib.reload( TKCM_Util )

#############################################################################################################################
#OpenMaya2.0を使用したプラグインであることを宣言する
def maya_useNewAPI():
    pass;

##########################################################################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################
## カスタムコマンド

class cmd_create_joints_on_mesh_components(om2.MPxCommand):
    # コマンド名
    kPluginCmdName = "createJointsOnMeshComponents"

    #########################################################################################################################
    ## コア
    def doIt(self, args):
        
        flagValues = self.parseArguments( args ); # フラグの確認と値の取得を行う
        
        ##################################################################################
        ## 処理
        create_joint_count = 0 # 生成するジョイントの数を指定する変数（root,tipを含んだ数）

        # コンポーネントの選択順にIDリストを取得するためのオプションを有効にする
        if mel.eval("selectPref -query -trackSelectionOrder") == False:
            mel.eval("selectPref -trackSelectionOrder true");
        
        # 処理対象とするメッシュのデータを取得する
        sel_list = om2.MGlobal.getActiveSelectionList();
        valid, sel_comp_ids, sel_mesh = ParseSelectionList(sel_list)
        if valid == False:  # ターゲットメッシュの確認と値の取得を行う
            return False;
        create_joint_count = len(sel_comp_ids) 

        # コンポーネントのタイプごとに位置と法線の情報を取得する
        sel_comp_type = TKCM_Util.selectedComponentType(sel_list, 0);
        poi_pos_array, poi_nml_array = GetComponentPosAndNml(sel_comp_type, sel_comp_ids, sel_mesh)
        
        # 等分割の場合は再計算
        if flagValues["-createType"] == 1: # evenly intervalタイプの場合
            poi_pos_array, poi_nml_array = RecomputeIntervalPosAndNml(flagValues["-createCount"], poi_pos_array, poi_nml_array)
            create_joint_count = len(poi_pos_array)
        
        # 回転値を算出するためのデータ（DirectionとUpvector）をコンポーネント間の位置情報から算出する(配列の要素末尾は1つ前の値のコピーを入れておく)
        poi_dir_array = GetChainPoiDirection(poi_nml_array, poi_pos_array);

        # ジョイントチェインを作成する
        rest_parent_g_quat = om2.MQuaternion();
        rest_joint_root_path = "";
        for i in range (create_joint_count) :
            # ルート/ティップのジョイント生成をするかのフラグの対応
            if i == 0 and flagValues["-createRootjoint"] == False:
                continue; # ルートジョイントの作成をスキップ
            if i == create_joint_count-1 and flagValues["-createTipJoint"] == False:
                continue; # ティップジョイントの作成をスキップ

            # ジョイントを生成する向きを算出する
            joint_g_quat = TKCM_Util.quaternionFromDirectionAndUpvector(poi_dir_array[i], poi_nml_array[i], flagValues["-axisType"], flagValues["-aimAxisNeg"], flagValues["-upAxisNeg"]); # ジョイントのグローバル回転値（Quat）を算出する
            joint_l_quat = joint_g_quat * rest_parent_g_quat.inverse(); # 前回の計算結果（＝親ジョイントのグローバル回転）を元にローカル回転を算出する
            joint_rad3 = joint_l_quat.asEulerRotation(); # QuatをEuler(radian)へ変換する
            joint_deg3 = TKCM_Util.toDeg3(joint_rad3); # チャンネルボックスにセットする回転値が必要なのでEuler(degree)に変換する
            
            pos_str = TKCM_Util.toMelString(om2.MVector(poi_pos_array[i])); # 数値をmel用の文字列に変換する 例：(1,2,3) -> '1 2 3 '

            # jointコマンドを実行（位置はグローバル値、回転はローカル値をセットする）
            if flagValues["-setOnJointOrient"] :
                ori_str = TKCM_Util.toMelString(joint_deg3); # 数値をmel用の文字列に変換する 例：(1,2,3) -> '1 2 3 '
                joint_name = mel.eval("joint -position " + pos_str + " -orientation " + ori_str );
            else:
                joint_deg3_str = list(map(str, joint_deg3)); # 文字列のリストにしておく　例：(1,2,3) -> ['1','2','3']
                joint_name = mel.eval("joint -position " + pos_str + " -angleX " + joint_deg3_str[0] + " -angleY " + joint_deg3_str[1] + " -angleZ " + joint_deg3_str[2] );

            # 次の計算のために現在のグローバル回転値を保存しておく
            rest_parent_g_quat = joint_g_quat; 
            # ジョイントチェインのルートジョイントのパスを記録しておく
            if len(rest_joint_root_path) == 0:
                rest_joint_root_path = joint_name;

        # ジョイントチェインのルートジョイントを選択状態にして終了
        mel.eval("select -r " + rest_joint_root_path);
        mel.eval("parent -w");

    #########################################################################################################################
    ## 書式やソースデータのチェックを行いつつ、必要な情報をメンバー変数に格納する
    
    # 書式（フラグ）の確認を行いつつ、フラグの値をメンバー変数に格納する
    def parseArguments(self, args) -> dict:
        # コマンドの書式をチェックする
        try: 
            argData = om2.MArgDatabase (self.syntax(), args);
        except: 
            om2.MGlobal.displayError("syntax error: not enough arguments");
            pass;
        
        result = {};
        # フラグの値を取得する ( [キー] = フラグの値　if フラグが存在するか確認 else フラグが無かった際に使用する基本値 )
        result["-setOnJointOrient"] =argData.flagArgumentBool("setOnJointOrient", 0) if argData.isFlagSet("setOnJointOrient") else False;
        result["-createRootjoint"]  =argData.flagArgumentBool("createRootjoint", 0) if argData.isFlagSet("createRootjoint") else True;
        result["-createTipJoint"]   =argData.flagArgumentBool("createTipJoint", 0) if argData.isFlagSet("createTipJoint") else True;
        result["-createType"]       =argData.flagArgumentInt("createType", 0) if argData.isFlagSet("createType") else 0; # 0=on centor of component, 1=evenly interval
        result["-createCount"]      =argData.flagArgumentInt("createCount", 0) if argData.isFlagSet("createCount") else 0; # 生成するジョイント数を指定する（createType==1の時に使用）
        result["-axisType"]         =argData.flagArgumentInt("axisType", 0) if argData.isFlagSet("axisType") else 3; # 0=ZY, 1=ZX, 2=XZ, 3=XY, 4=YX, 5=YZ
        result["-aimAxisNeg"]       =argData.flagArgumentBool("aimAxisNeg", 0) if argData.isFlagSet("aimAxisNeg") else False;
        result["-upAxisNeg"]        =argData.flagArgumentBool("upAxisNeg", 0) if argData.isFlagSet("upAxisNeg") else False;

        return result;

    #########################################################################################################################
    ## カスタムコマンド専用の関数

    def __init__(self):
        om2.MPxCommand.__init__(self);

    @staticmethod
    def cmdCreator():
        return cmd_create_joints_on_mesh_components();

    # コマンドのフラグ書式を設定する
    @staticmethod
    def syntaxCreator() -> om2.MSyntax:
        # addFlag(フラグのショートネーム, ロングネーム, データ型)　で記述する
        syntax = om2.MSyntax();
        syntax.addFlag( "jo", "setOnJointOrient", om2.MSyntax.kBoolean );
        syntax.addFlag( "rj", "createRootjoint", om2.MSyntax.kBoolean );
        syntax.addFlag( "tj", "createTipJoint", om2.MSyntax.kBoolean );
        syntax.addFlag( "ct", "createType", om2.MSyntax.kLong );
        syntax.addFlag( "cc", "createCount", om2.MSyntax.kLong );
        syntax.addFlag( "at", "axisType", om2.MSyntax.kLong );
        syntax.addFlag( "aan", "aimAxisNeg", om2.MSyntax.kBoolean );
        syntax.addFlag( "uan", "upAxisNeg", om2.MSyntax.kBoolean );

        return syntax;

##########################################################################################################################################################################################################################################################
# ソースデータに不足がないか確認を行い、選択状態のメッシュとコンポーネントIDのリストを取得する
def ParseSelectionList(sel_list: om2.MSelectionList) -> [bool, om2.MIntArray, om2.MFnMesh]:
    if sel_list.length() != 1:
        print(TKCM_Util.getCodeLocation()); # 選択が複数ある、もしくは選択が無い
        return [False, om2.MIntArray(), om2.MFnMesh()];

    sel_dagPath, sel_obj = sel_list.getComponent (0);
    if sel_dagPath.hasFn(om2.MFn.kMesh) == False:
        print(TKCM_Util.getCodeLocation()); # メッシュデータが選択されていない
        return [False, om2.MIntArray(), om2.MFnMesh()];

    # 選択したコンポーネントのIDを取得する（選択した順）
    sel_comp_ids = TKCM_Util.getSelectedComponentIds(sel_list, 0, True);
    if len(sel_comp_ids) < 2:
        print(TKCM_Util.getCodeLocation()); # コンポーネントの選択数が不足している
        return [False, om2.MIntArray(), om2.MFnMesh()];

    target_mesh = om2.MFnMesh(sel_dagPath);
    return [True, sel_comp_ids, target_mesh];

# コンポーネントのタイプごとにコンポーネントの中央位置と法線の情報を取得する
def GetComponentPosAndNml(comp_type:TKCM_Util.MeshCompType, component_id:om2.MIntArray, target_mesh:om2.MFnMesh, space :om2.MSpace = om2.MSpace.kWorld) -> [om2.MPointArray(), om2.MVectorArray()]:
    poi_pos_array = om2.MPointArray();
    poi_nml_array = om2.MVectorArray();
    if comp_type == TKCM_Util.MeshCompType.kVertex:
        # 頂点モード
        all_poi_nml = target_mesh.getNormals(space);
        for compID in component_id:
            poi_pos_array.append(target_mesh.getPoint(compID, space));
            poi_nml_array.append(all_poi_nml[compID]);
    elif comp_type == TKCM_Util.MeshCompType.kEdge:
        # エッジモード
        all_poi_nml = target_mesh.getNormals(space);
        for compID in component_id:
            vtx0, vtx1 = target_mesh.getEdgeVertices(compID);

            pos = ( om2.MVector(target_mesh.getPoint(vtx0, space)) + om2.MVector(target_mesh.getPoint(vtx1, space)) ) * 0.5; # エッジの中央位置を算出する
            poi_pos_array.append(om2.MPoint(pos));
            nml = ( all_poi_nml[vtx0] + all_poi_nml[vtx0] ) * 0.5; # エッジの両端の頂点法線の中央位置を算出する
            poi_nml_array.append(nml);
    elif comp_type == TKCM_Util.MeshCompType.kFace:
        # フェースモード
        for compID in component_id:
            vtxIDs = target_mesh.getPolygonVertices(compID);

            # フェースの中央位置を算出する
            pos = om2.MPoint();
            for vtx in vtxIDs:
                pos += om2.MPoint(target_mesh.getPoint(vtx, space));
            poi_pos_array.append(pos/len(vtxIDs));
            poi_nml_array.append(target_mesh.getPolygonNormal(compID, space));
    return [poi_pos_array, poi_nml_array]

# 頂点位置リストを元にして次の頂点への向きを返す（算出した向きと頂点法線が平行になる場合は、法線リストを微調整する）
def GetChainPoiDirection(io_chain_poi_nml:om2.MVectorArray, chain_poi_pos:om2.MVectorArray) -> om2.MVectorArray:
    poi_dir_array = om2.MVectorArray();
    for i in range (len(chain_poi_pos) - 1) :
        dir = ( chain_poi_pos[i+1] - chain_poi_pos[i] ).normal();
        poi_dir_array.append(dir);
    poi_dir_array.append(poi_dir_array[-1]);
    # ディレクションと法線の向きが平行の場合は回転値の計算が出来ないため予め対処しておく
    for i in range (len(io_chain_poi_nml)) :
        if poi_dir_array[i].isParallel(io_chain_poi_nml[i]):
            # 平行と判定された場合は前後の値を用いて法線の値を微調整しておく
            lerpVal = (io_chain_poi_nml[i] + io_chain_poi_nml[i-1]) * 0.5 if i == len(io_chain_poi_nml)-1 else (io_chain_poi_nml[i] + io_chain_poi_nml[i+1]) * 0.5;
            io_chain_poi_nml[i] = lerpVal.normal();
    return poi_dir_array

def RecomputeIntervalPosAndNml(div_count:int, poi_pos_array:om2.MPointArray(), poi_nml_array:om2.MVectorArray())->[om2.MPointArray(), om2.MVectorArray()]:
    interval_pos_array = om2.MPointArray()
    interval_nml_array = om2.MVectorArray()
    # コンポーネント間の距離を算出しておく（リストは[0]=0.0スタートの加算式で配列の要素末尾が全長値となる）
    length_pack = om2.MFloatArray(1, 0.0);
    for i in range (len(poi_pos_array) - 1) :
        length = TKCM_Util.getDistanceAtoB(poi_pos_array[i], poi_pos_array[i+1]);
        length_pack.append(length_pack[-1] + length);
    
    e = length_pack[-1]/(div_count+1);
    interval_pos_array.append(poi_pos_array[0])
    interval_nml_array.append(poi_nml_array[0])
    for i in range (div_count+1) :
        if i==0:
            continue
        tree_i, remainder = TKCM_Util.binarySearchTree(length_pack, e*i)
        t = remainder / (length_pack[tree_i+1] - length_pack[tree_i])
        p = TKCM_Util.lerp_MPoint(poi_pos_array[tree_i], poi_pos_array[tree_i+1], t)
        n = TKCM_Util.lerp_MVector(poi_nml_array[tree_i], poi_nml_array[tree_i+1], t)
        interval_pos_array.append(p)
        interval_nml_array.append(n)
    interval_pos_array.append(poi_pos_array[-1])
    interval_nml_array.append(poi_nml_array[-1])

    return [interval_pos_array, interval_nml_array]
    
##########################################################################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################
## カスタムマニピュレータを介したデバッグドローイング

# カスタムマニピュレータ
class CJOMC_DummyManip (omUI.MPxManipulatorNode):
    kNodeName = 'CJOMC_DummyContextManip'
    kTypeId = om2.MTypeId( 0x00081162 )

    def __init__(self):
        omUI.MPxManipulatorNode.__init__(self)

        self.drawHandleName = -1
        self.components_pos = om2.MPointArray()
        self.axis_type = 3

    @classmethod
    def creator(cls):
        return cls()

    @classmethod
    def initialize(cls):
        pass

    # virtual
    def postConstructor(self):
        gl_pickable_item = self.glFirstHandle()
        self.drawHandleName = gl_pickable_item

    # virtual
    def preDrawUI(self, view):
        pass

    # virtual
    def drawUI(self, draw_manager, frame_context):
        # コンポーネントの順番を描画
        draw_manager.beginDrawable(omR.MUIDrawManager.kNonSelectable, self.drawHandleName)
        self.setHandleColor(draw_manager, self.drawHandleName, self.selectedColor())
        draw_manager.setFontSize(25)
        draw_manager.text(om2.MPoint(self.poi_pos_array[i]), str(i), omR.MUIDrawManager.kLeft)
        draw_manager.endDrawable()

        # コンポーネントを繋ぐ点線を描画
        draw_manager.beginDrawable(omR.MUIDrawManager.kNonSelectable, self.drawHandleName)
        self.setHandleColor(draw_manager, self.drawHandleName, self.selectedColor())
        draw_manager.setLineStyle(omR.MUIDrawManager.kShortDashed)
        draw_manager.lineStrip(self.poi_pos_array, False)
        draw_manager.endDrawable()

        # ジョイントの作成候補の座標を描く
        axis_colors = [self.xColor(), self.yColor()]
        if self.axis_type==0:
            axis_colors = [self.zColor(), self.yColor()]
        elif self.axis_type==1:
            axis_colors = [self.zColor(), self.xColor()]
        elif self.axis_type==2:
            axis_colors = [self.xColor(), self.zColor()]
        elif self.axis_type==3:
            axis_colors = [self.xColor(), self.yColor()]
        elif self.axis_type==4:
            axis_colors = [self.yColor(), self.xColor()]
        elif self.axis_type==5:
            axis_colors = [self.yColor(), self.zColor()]
        draw_manager.beginDrawable(omR.MUIDrawManager.kNonSelectable, self.drawHandleName)
        self.setHandleColor(draw_manager, self.drawHandleName, axis_colors[0])
        draw_manager.setLineWidth(3)
        draw_manager.lineList(self.aim_axis_array, False)
        draw_manager.endDrawable()
        draw_manager.beginDrawable(omR.MUIDrawManager.kNonSelectable, self.drawHandleName)
        self.setHandleColor(draw_manager, self.drawHandleName, axis_colors[1])
        draw_manager.setLineWidth(3)
        draw_manager.lineList(self.up_axis_array, False)
        draw_manager.endDrawable()

# カスタムマニピュレータを登録するコンテキスト
class CJOMC_DummyManipContext(omUI.MPxSelectionContext):
    @classmethod
    def creator(cls):
        return cls()

    def __init__(self, draw_joint:bool, create_type:int, create_count_:int, root:bool, tip:bool, axis_type:int, aim_neg:bool, up_neg:bool):
        omUI.MPxSelectionContext.__init__(self)
        self.setTitleString('Plug-in create_joints_on_mesh_components dummy manipulator')

        self.kContextName = 'CJOMC_DummyManipContext'
        self.manipulator_class_ptr = None
        self.call_back_id = -1
        self.pass_flag_draw = False
        self.pass_draw_joint = draw_joint
        self.pass_axis_type = axis_type

        ##############################################################################################################################################
        ## マニピュレータの新規作成時に描画を決定するために、描画に必要なデータをこのタイミングで算出しておく
        ## update_manipulators()が常にコールされるのでマニピュレータの描画が新規作成されるため
        # 処理対象とするメッシュのデータを取得する
        self.sel_list = om2.MGlobal.getActiveSelectionList();
        valid, sel_comp_ids, sel_mesh = ParseSelectionList(self.sel_list)
        # コンポーネントのタイプごとに位置と法線の情報を取得する
        sel_comp_type = TKCM_Util.selectedComponentType(self.sel_list, 0);
        self.pass_poi_pos_array, joint_nml_array = GetComponentPosAndNml(sel_comp_type, sel_comp_ids, sel_mesh)
        joint_pos_array=om2.MPointArray()
        joint_pos_array.copy(self.pass_poi_pos_array)
        # 頂点間の距離を算出して最短の値を保持する
        min_length=float('inf')
        for i in range(len(joint_pos_array)-1):
            length = TKCM_Util.getDistanceAtoB(joint_pos_array[i], joint_pos_array[i+1]);
            min_length = min_length if min_length < length else length
        # 等分割の場合は再計算
        if create_type == 1: # evenly intervalタイプの場合
            joint_pos_array, joint_nml_array = RecomputeIntervalPosAndNml(create_count_, joint_pos_array, joint_nml_array)
            min_length = TKCM_Util.getDistanceAtoB(joint_pos_array[0], joint_pos_array[1]);
        
        # 回転値を算出するためのデータ（DirectionとUpvector）をコンポーネント間の位置情報から算出する(配列の要素末尾は1つ前の値のコピーを入れておく)
        joint_dir_array = GetChainPoiDirection(joint_nml_array, joint_pos_array);
        # ジョイントの座標ラインを描くための頂点リストを作る
        self.pass_aim_axis_array = om2.MPointArray()
        self.pass_up_axis_array = om2.MPointArray()
        joint_size = min_length * 0.25
        aim_size = joint_size * -1 if aim_neg else joint_size
        up_size = joint_size * -1 if up_neg else joint_size
        other_size = joint_size * 0.5
        if draw_joint:
            for i in range(len(joint_dir_array)):
                if i==0 and root==False:
                    continue
                if i==len(joint_dir_array)-1 and tip==False:
                    continue
                self.pass_aim_axis_array.append(joint_pos_array[i])
                self.pass_aim_axis_array.append(joint_pos_array[i] + (joint_dir_array[i] * aim_size ) )

                self.pass_up_axis_array.append(joint_pos_array[i])
                up = (joint_dir_array[i]^(joint_nml_array[i]))^(joint_dir_array[i])
                self.pass_up_axis_array.append(joint_pos_array[i] + (up * up_size) )

                self.pass_aim_axis_array.append(joint_pos_array[i] + (joint_dir_array[i] * aim_size * 0.5 ) )
                self.pass_aim_axis_array.append(TKCM_Util.lerp_MVector(self.pass_aim_axis_array[-1], joint_pos_array[i] + (up * up_size * 0.5), 0.85 ))
        ##############################################################################################################################################

    def toolOnSetup(self, event):
        self.setHelpString('dummy manipulator')
        CJOMC_DummyManipContext.update_manipulators(self)
        self.call_back_id = om2.MModelMessage.addCallback( om2.MModelMessage.kActiveListModified, CJOMC_DummyManipContext.update_manipulators, self)

    def toolOffCleanup(self):
        om2.MModelMessage.removeCallback(self.call_back_id)
        self.call_back_id = -1

        omUI.MPxSelectionContext.toolOffCleanup(self)

    @staticmethod
    def update_manipulators(ctx):
        ctx.deleteManipulators()

        # Clear info
        ctx.manipulator_class_ptr = None
        ctx.first_object_selected = om2.MObject.kNullObj
        
        (manipulator, manip_object) = CJOMC_DummyManip.newManipulator('CJOMC_DummyContextManip')
        if manipulator:
            # Add the manipulator
            ctx.addManipulator(manip_object)

            # Save state
            ctx.manipulator_class_ptr = manipulator
            # 予め取得しておいたデバッグドローイング用の座標データをマニピュレータに渡す
            ctx.manipulator_class_ptr.poi_pos_array = ctx.pass_poi_pos_array
            ctx.manipulator_class_ptr.aim_axis_array = ctx.pass_aim_axis_array
            ctx.manipulator_class_ptr.up_axis_array = ctx.pass_up_axis_array
            ctx.manipulator_class_ptr.axis_type = ctx.pass_axis_type

# コンテキスト登録コマンド
class CJOMC_DummyManipContextCmd (omUI.MPxContextCommand):
    kPluginCmdName = "CreateJointsOnMeshComponentsDraw"

    def __init__(self):
        omUI.MPxContextCommand.__init__(self)
        self.context_ptr = None
        self.flag_draw = False
        self.components_pos = om2.MPointArray()

    @staticmethod
    def creator():
        return CJOMC_DummyManipContextCmd()
    
    def appendSyntax(self):
        theSyntax = self.syntax()
        theSyntax.addFlag("jd", "joint_draw", om2.MSyntax.kBoolean)
        theSyntax.addFlag("ct", "create_type", om2.MSyntax.kLong)
        theSyntax.addFlag("cc", "create_count", om2.MSyntax.kLong)
        theSyntax.addFlag("cr", "create_root", om2.MSyntax.kBoolean)
        theSyntax.addFlag("ct", "create_tip", om2.MSyntax.kBoolean)
        theSyntax.addFlag("at", "axis_type", om2.MSyntax.kLong)
        theSyntax.addFlag("an", "aim_neg", om2.MSyntax.kBoolean)
        theSyntax.addFlag("un", "up_neg", om2.MSyntax.kBoolean)
    
    def makeObj(self):
        theParser = self.parser()
        joint_draw_ = theParser.flagArgumentBool("joint_draw", 0) if theParser.isFlagSet("joint_draw") else True
        create_type_ = theParser.flagArgumentInt("create_type", 0) if theParser.isFlagSet("create_type") else 0
        create_count_ = theParser.flagArgumentInt("create_count", 0) if theParser.isFlagSet("create_count") else 1
        root_ = theParser.flagArgumentBool("create_root", 0) if theParser.isFlagSet("create_root") else True
        tip_ = theParser.flagArgumentBool("create_tip", 0) if theParser.isFlagSet("create_tip") else True
        axis_type_ = theParser.flagArgumentInt("axis_type", 0) if theParser.isFlagSet("axis_type") else 3
        aim_neg_ = theParser.flagArgumentBool("aim_neg", 0) if theParser.isFlagSet("aim_neg") else True
        up_neg_ = theParser.flagArgumentBool("up_neg", 0) if theParser.isFlagSet("up_neg") else True
        self.context_ptr = CJOMC_DummyManipContext(joint_draw_, create_type_, create_count_, root_, tip_, axis_type_, aim_neg_, up_neg_) 
        return self.context_ptr

    def doEditFlags(self):
        """
        makeObj()の後に実行する処理
        """
        return

##########################################################################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################
## プラグイン登録

def initializePlugin(mobject):
    pluginFn = om2.MFnPlugin(mobject);
    pluginFn.registerCommand(cmd_create_joints_on_mesh_components.kPluginCmdName, cmd_create_joints_on_mesh_components.cmdCreator, cmd_create_joints_on_mesh_components.syntaxCreator);
    pluginFn.registerContextCommand( CJOMC_DummyManipContextCmd.kPluginCmdName, CJOMC_DummyManipContextCmd.creator)
    pluginFn.registerNode( CJOMC_DummyManip.kNodeName, CJOMC_DummyManip.kTypeId, CJOMC_DummyManip.creator, CJOMC_DummyManip.initialize, om2.MPxNode.kManipulatorNode)

def uninitializePlugin(mobject):
    pluginFn = om2.MFnPlugin(mobject);
    pluginFn.deregisterCommand(cmd_create_joints_on_mesh_components.kPluginCmdName);
    pluginFn.deregisterContextCommand(CJOMC_DummyManipContextCmd.kPluginCmdName)
    pluginFn.deregisterNode(CJOMC_DummyManip.kTypeId)