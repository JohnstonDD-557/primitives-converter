# 插件使用说明

## 阅前提示

这份说明仅为插件的基本使用说明,并不会详细介绍改模相关的操作步骤。\
如果需要改模步骤相关说明,请移步[战舰世界MOD改模流程展示](https://www.bilibili.com/video/BV1mwcweVEs7/),[【战舰世界】建模教学](https://www.bilibili.com/video/BV1dN411a7QN/)等教程。

## 安装

在releases中下载最新的插件压缩包,启动Blender(目前最高版本支持Blender 3.6)\
按图中所示(编辑-->偏好设置-->插件-->安装)打开插件安装界面:\
![打开安装界面](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/Install_addon_1.png)\
打开安装界面后找到下载下来的插件压缩包,进行安装:\
![安装插件](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/Install_addon_2.png)\
在插件管理界面看到图中所示插件说明安装完成:\
![安装完成](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/Install_addon_3.png)\
至此,插件安装完成,但保险起见,建议重启Blender后再开始后面的操作。

## 模型导入

导入模型需要准备*.primitive文件(来自于早期wows文件备份或由该插件导出)和*.visual文件(Wargaming wows 14.1更新前的visual文件或由该插件导出的visual文件,可从之前的[modSDK](https://github.com/wgmods/ModSDK/releases/tag/13.11.0)中获得),要求名称相同且位于同一目录下,如下图所示:\
![导入模型_文件准备](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/InputModel_Files.png)\
接下来,启动Blender,按下图所示(文件->导入->World of Warships Bigworld Model)打开导入界面:\
![导入模型](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/InputModel_1.png)\
然后可以看到导入的界面如下,找到需要导入的primitive文件:\
![导入界面](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/InputModel_2.png)\
点击'Import model',即可导入模型,导入成功后界面如下图所示:\
![导入成功](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/InputModel_3.png)\
到这里,就成功把pri文件导入到Blender中了,尽管大多数情况下,合适的pri文件和visual文件可能来自于自己导出的模型,直接导入pri模型的功能并不常用。

## 模型导出

导出模型,需要模型与空物体之间的层级符合一定的结构,如下图:\
![导出模型_模型层级](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/OutputModel_1.png)\
空物体均为纯轴,第一个层级均为```Scene Root```,假设你有一个打算称为```AAA```的模型需要导出,则模型的层级结构需为:\
|空物体(纯轴):Scene Root\
|    |空物体(纯轴):AAA\
|    |网格物体:AAAShape\
可以看出,打算导出的网格物体与轴之间需要一一对应,网格物体的名称需要在对应轴名称的基础上增加```Shape```

对于网格物体本身,也有要求,首先需要选中网格物体,打开```材质```栏,会看到下图的信息(如果没有则需要为物体新建材质):\
![导出模型_材质](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/OutputModel_2.png)\
这里需要修改材质的名称,任意英文名称均可。然后填写BigWorld Material中的```格式```和```mfm```项。\
***格式***:\
对于无权重模型,可以使用xyznuv(透明模型),xyznuvr(线缆),xyznuvtb(各种常规模型,不知道用什么格式的都可以直接使用该格式)\
对于有权重模型,则需使用xyznuviiiwwtb,对于此种格式,模型与空物体之间的层级会稍有不同,其他地方的处理也稍麻烦些,但这里暂时不做介绍。\
***mfm***:\
这里需要填写该模型使用的mfm文件的路径,形如```PnfMods/ *** / *** / *** /AAA.mfm```

处理完材质部分,接下来打开数据栏,找到```UV贴图```,将UV贴图的名称修改为```uv1```,如下图,如果模型有多个UV贴图,则需要先进行拆分或合并。\
![导出模型_UV](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/OutputModel_3.png)\

最后,检查网格模型是否已经三角化,保证模型的所有面均为三角面后,即可在***物体模式***下选择```Secent Root```,打开导出界面(文件->导出->World of Warships Bigworld Model):\
![导出模型](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/OutputModel_4.png)\
在导出界面,只需要选择需要导出的位置和名称,即可导出模型,如下:\
![导出界面](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/OutputModel_5.png)\
![导出成功](https://raw.githubusercontent.com/JohnstonDD-557/johnston_dd557.github.io/refs/heads/main/2/OutputModel_6.png)\
可以看到导出了4份文件,其中```.temp_model```无实际用途,可以无视,```.visual```为旧版本(14.1以前)格式的visual文件,用于后期可能重新导入该模型,```.visual.fix```为新版本(14.1以后)格式的visual文件,```.primitive```为导出的模型文件,可以使用ModSDK中的geometrypack打包为WoWs可以读取的```.geometry```文件。\
至此,就成功把模型导出为可以被WoWs读取的格式了。

## 注意事项
