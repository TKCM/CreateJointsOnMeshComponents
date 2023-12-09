# CreateJointsOnMeshComponents

メッシュのコンポーネントの座標を元にしてジョイントチェインを作成するツールです。
![create_joints_on_mesh_components](https://github.com/TKCM/CreateJointsOnMeshComponents/assets/13941074/a141c288-b8ce-4830-aada-5044baeee14a)

## 起動
```
import maya.cmds as cmds
import tools.create_joints_on_mesh_components_tool as CJOMCTool

cmds.loadPlugin( 'create_joints_on_mesh_components.py', quiet=True )
CJOMCTool.run()
```
![image](https://github.com/TKCM/CreateJointsOnMeshComponents/assets/13941074/9ed910d8-cfad-4de6-980f-f0ee9725223b)

