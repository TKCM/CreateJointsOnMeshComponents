###################################################################################################################################
###################################################################################################################################
# モジュール
import inspect
import re
import math
from enum import Enum
from typing import Literal

# Mayaモジュール
from maya import cmds
import maya.mel as mel
import maya.api.OpenMaya as om2
###################################################################################################################################
###################################################################################################################################

class MeshCompType(Enum):
    kNon = -1
    kFaceVertex = 0
    kVertex = 1
    kEdge = 2
    kFace = 3    

def selectedComponentType(selection_list: om2.MSelectionList, id: int) -> MeshCompType:
    _, comp_obj = selection_list.getComponent (id);
    if comp_obj.hasFn(om2.MFn.kMeshVertComponent):
        return MeshCompType.kVertex;
    elif comp_obj.hasFn(om2.MFn.kMeshEdgeComponent):
        return MeshCompType.kEdge;
    elif comp_obj.hasFn(om2.MFn.kMeshPolygonComponent):
        return MeshCompType.kFace;
    elif comp_obj.hasFn(om2.MFn.kMeshFaceVertComponent):
        return MeshCompType.kFaceVertex;
    else:
        return MeshCompType.kNon;

def getSelectedComponentIds(selection_list: om2.MSelectionList, id: int, orderedSelection: bool =False) -> om2.MIntArray:
    if orderedSelection:
        orderedIDs = om2.MIntArray();
        sel_comp_str = str( mel.eval("ls -orderedSelection -flatten") );

        p = Literal;
        comp_type = selectedComponentType(selection_list, id);
        for s in sel_comp_str.split(", "):
            if comp_type == MeshCompType.kVertex:
                p = r'vtx\[(.*)\]\'';
            elif comp_type == MeshCompType.kEdge:
                p = r'e\[(.*)\]\'';
            elif comp_type == MeshCompType.kFace:
                p = r'f\[(.*)\]\'';
            m = re.findall(p, s); #大カッコ[]の間の文字列を取得する
            orderedIDs.append(int(str(m[0])));
        return orderedIDs;
    else:
        if selectedComponentType(selection_list, id) == -1:
            return om2.MIntArray(0);
        else:
            _, comp_obj = selection_list.getComponent (id);
            comp_id_array = om2.MFnSingleIndexedComponent(comp_obj);
            return comp_id_array.getElements();
        

class MatrixType(Enum):
    worldMatrix = 0
    worldInverseMatrix = 1
    parentMatrix = 2
    parentInverseMatrix = 3
    matrix = 4
    inverseMatrix = 5
    dagLocalMatrix = 6
    dagLocalInverseMatrix = 7
    
def getSelectedTransform(selection_list: om2.MSelectionList, id: int, matrix_type: MatrixType) -> om2.MMatrix:
    dgObj = selection_list.getDependNode(id);
    dg = om2.MFnDependencyNode(dgObj);
    attrObj = dg.attribute(matrix_type.name);
    plug = om2.MPlug(dgObj, attrObj);
    if matrix_type.value <= 3: 
        plug = plug.elementByLogicalIndex(0);
    matData = om2.MFnMatrixData(plug.asMObject());
    print(matrix_type.name);
    return matData.matrix();

def quaternionFromDirectionAndUpvector(direction: om2.MVector, upvector: om2.MVector, axis_type:int, aim_axis_neg:bool, up_axis_neg:bool) -> om2.MQuaternion:
    up_neg_ = -1 if up_axis_neg else 1

    v0 = direction.normal().__neg__() if aim_axis_neg else direction.normal()
    v1 = ( (v0 ^ (upvector.normal()) ) ^ ( v0 ) ).normal() * up_neg_;
    # Mat3x3を作成する
    if axis_type == 0:
        xAxis = (v1^v0).normal()
        yAxis = v1
        zAxis = v0
    elif axis_type == 1:
        xAxis = v1
        yAxis = (v1^v0).normal().__neg__()
        zAxis = v0
    elif axis_type == 2:
        xAxis = v0
        yAxis = (v1^v0).normal()
        zAxis = v1
    elif axis_type == 3:
        xAxis = v0
        yAxis = v1
        zAxis = (v1^v0).normal().__neg__()
    elif axis_type == 4:
        xAxis = v1
        yAxis = v0
        zAxis = (v1^v0).normal()
    elif axis_type == 5:
        xAxis = (v1^v0).normal().__neg__()
        yAxis = v0
        zAxis = v1

    rotMat = om2.MMatrix([[xAxis.x, xAxis.y, xAxis.z, 0.0], [yAxis.x, yAxis.y, yAxis.z, 0.0], [zAxis.x, zAxis.y, zAxis.z, 0.0], [0.0, 0.0, 0.0, 0.0]]);

    # Quatに変換してから返す
    result = om2.MQuaternion();
    result.setValue(rotMat);
    return result;

def getCodeLocation() -> [str, str, int]:
    frame = inspect.currentframe().f_back;
    return [frame.f_code.co_filename, frame.f_code.co_name, frame.f_lineno];

def getDistanceAtoB(vecA: om2.MFloatVector, vecB: om2.MFloatVector) -> float:
    return (vecA-vecB).length();

def toMelString(val) -> str:
    # 例：(1, 2, 3) -> "1 2 3 "
    tbl = str.maketrans({'(': '', ',': '', ')': ' '}); # 変換テーブルを作成する
    return str(val).translate(tbl);

def toDeg3(radian: om2.MEulerRotation) ->(float, float, float):
    return (math.degrees(radian.x), math.degrees(radian.y), math.degrees(radian.z));

def binarySearchTree(tree, key) -> [int, float]:
    lowID = 1
    highID = len(tree)
    # テーブル内を2分割しながら検索 
    while lowID < highID:
        midID = int(( lowID + highID ) / 2)
        if tree[midID] <= key:
            lowID = midID + 1
        else:
            highID = midID
    remainder = key - tree[lowID - 1]
    return [lowID - 1, remainder]

def lerp_MVector(this:om2.MVector, other:om2.MVector, t:float)->om2.MVector:
    return this + ( ( other - this ) * t )

def lerp_MPoint(this:om2.MPoint, other:om2.MPoint, t:float)->om2.MPoint:
    result_x = this.x + ( ( other.x - this.x ) * t )
    result_y = this.y + ( ( other.y - this.y ) * t )
    result_z = this.z + ( ( other.z - this.z ) * t )
    result_w = this.w + ( ( other.w - this.w ) * t )
    return om2.MPoint(result_x, result_y, result_z, result_w)