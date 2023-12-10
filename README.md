# CreateJointsOnMeshComponents

メッシュのコンポーネントの座標を元にしてジョイントチェインを作成するツールです。
![create_joints_on_mesh_components](https://github.com/TKCM/CreateJointsOnMeshComponents/assets/13941074/a141c288-b8ce-4830-aada-5044baeee14a)

## How to run tool
```
import maya.cmds as cmds
import tools.create_joints_on_mesh_components_tool as CJOMCTool

cmds.loadPlugin( 'create_joints_on_mesh_components.py', quiet=True )
CJOMCTool.run()
```

## main UI
![image](https://github.com/TKCM/CreateJointsOnMeshComponents/assets/13941074/9ed910d8-cfad-4de6-980f-f0ee9725223b)

### Regist Mesh Components
選択中のメッシュのコンポーネントをツールに登録します。  
コンポーネントの選択は２つ以上必要です。

### re-select
ツールに登録していたコンポーネントを再び選択状態にします。  
シーン上に対象が見つからなかった場合、ツールはリセットされます。

### create type (combo box)
- On Component Center -- コンポーネントの中央にジョイントを生成する
- Evenly Interval -- コンポーネントを繋ぐライン上に等間隔にジョイントを生成する*  
*等間隔になるようにジョイントを生成するのではなく、コンポーネントを繋ぐライン上を等分割した位置にジョイントを生成します

### root joint
始点にジョイントを生成する場合はONにします

### tip joint
終点にジョイントを生成する場合はONにします

### division number
"create type"が"Evenly Interval"の場合に有効になります。  
ラインの分割数を指定します。

### Create Joints
ビューポート上に描画している座標ガイドに従ってジョイントを生成します。

## option UI
![image](https://github.com/TKCM/CreateJointsOnMeshComponents/assets/13941074/f6d4cf58-e347-467d-a3e1-8f334b258247)

### Joint Orient 0,0,0
生成するジョイントの向きをジョイントオリエントではなく回転値にセットする場合はONにします。

### joint axis type (combo box)
- Aim Axis -- ジョイントチェインで子ジョイントを生成する軸
- Up Axis -- コンポーネントの法線を適用する軸

### Aim Axis negative
"Aim Axis"を反転する場合はONにする

### Up Axis negative
"Up Axis"を反転する場合はONにする
