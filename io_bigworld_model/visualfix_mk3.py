# coding:utf-8

import os
import sys
import re
import importlib

importlib.reload(sys)
import warnings

warnings.filterwarnings("ignore")

import xml.etree.ElementTree as ET
from xml.dom import minidom


'''

对Blender的bigWorldIO插件导出的旧版本visual进行格式转换,转换为新版本visual文件(版本:World Of Warships 14.1)

'''

# __DEBUG__参数说明: 默认为True
# True:生成为.fix文件,不覆盖源文件
# False:直接生成为.visual文件,覆盖源文件
__DEBUG__ = True

# ShapeClear 参数说明:  默认为False
# 注:该功能未经过详细测试,使用时上方DEBUG最好为True;若节点命名中含有Shape,此功能无法正常运行
# True:自动清理renderSet.nodes.note中多出来的Shape字段
# False:不进行清理
ShapeClear = True

def prettify(elem):
    """
    将节点转换成字符串，并添加缩进。
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")


def file_extension(path):
    return os.path.splitext(path)[1]


def listFiles(dirPath):
    fileList = []
    for root, dirs, files in os.walk(dirPath):
        for fileObj in files:
            fileList.append(os.path.join(root, fileObj))
    return fileList


def visual_fix(path,Fix = True):
    # print('scaning')
    p1 = r"(PnFMods/[^/]*/[^/]*/)"          # PnFMods/***/***/
    p2 = r"(./[^\\]*\\)"                    # ./***\
    p3 = r"(PnFMods/[^/]*/[^/]*/[^/]*/)"    # PnFMods/***/***/***/
    # fileList = listFiles(fileDir)

    # 找到visual文件
    fileObj_v = path  # 不影响原变量
    flag_visual = 1  # 是否有visual文件
    i = 0  # render节点数目记录 用于后续lod节点写入
    name_v = []  # name节点所对应的值
    flag_old = 1  # 是否为新版本model

    FileAdderss_v = str(fileObj_v)  # 获取需新建visual文件的地址

    if Fix:
        FileAdderss_v = FileAdderss_v + '.fix'  # 增加.fix后缀 (便于测试)

    # 读取visual文件内容,以确认是否为新版本model文件
    # print('文件内容:', fileObj_v)
    xmlstring = fileObj_v
    tree_v = ET.parse(xmlstring)
    root_v = tree_v.getroot()
    
    # 检测是否为旧版本visual文件
    # 当前检测原理:检测内部是否有 新版本版本含有的skeleton节点
    for elem in root_v.iter('skeleton'):
        flag_old = 0

    if flag_old:
        # print('start')
        # 建立生成的visual文件基础
        n_root_v = ET.Element(root_v.tag)  # 创建需生成的visual文件的根节点
        n_skeleton_v = ET.SubElement(n_root_v, 'skeleton')  # 创建子节点 skeleton
        n_properties_v = ET.SubElement(n_root_v, 'properties')  # 创建子节点 properties
        n_boundingBox_v = ET.SubElement(n_root_v, 'boundingBox')  # 创建子节点 boundingBox
        n_renderSets_v = ET.SubElement(n_root_v, 'renderSets')  # 创建子节点 renderSets
        n_lods_v = ET.SubElement(n_root_v, 'lods')  # 创建子节点 lods

        # 读取第一级visual文件的node数据  后续层级均相同且新文件中无需重复
        n_node_v = root_v.find('node')
        n_skeleton_v.append(n_node_v)

        # 处理新出现的properties节点
        n_underwater_v = ET.SubElement(n_properties_v, 'underwaterModel')
        n_abovewater_v = ET.SubElement(n_properties_v, 'abovewaterModel')
        n_underwater_v.text = 'false'
        n_abovewater_v.text = 'true'

        # 处理boundingBox节点
        min_v = root_v.find('boundingBox').find('min')
        max_v = root_v.find('boundingBox').find('max')
        n_boundingBox_v.append(min_v)
        n_boundingBox_v.append(max_v)

        # 处理renderSets节点
        for elem in root_v.iter('renderSet'):
            n_renderSet_v = ET.SubElement(n_renderSets_v, 'renderSet')  # 在renderSets节点中生成新的renderSet节点
            # name节点处理
            name_v.append(elem.find('geometry').find('vertices').text)  # 找到name节点所对应的值
            name_v[i] = re.sub('\t*', '', name_v[i])  # 删去多余字符
            name_v[i] = re.sub('.vertices', '', name_v[i])
            n_name_v = ET.SubElement(n_renderSet_v, 'name')  # 生成name节点
            n_name_v.text = name_v[i]  # 写入name节点的值
            i = i + 1
            # treatAsWorldSpaceObject节点处理
            n_treatAsWorldSpaceObject_v = elem.find('treatAsWorldSpaceObject')  # 找出原文件中对应节点
            n_renderSet_v.append(n_treatAsWorldSpaceObject_v)  # 将子节点写入renderSet节点中
            # nodes节点处理
            n_r_nodes_v = ET.SubElement(n_renderSet_v, 'nodes')  # 建立子节点nodes
            for node in elem.iter('node'):
                if ShapeClear:
                    node.text = re.sub('Shape', '', node.text)
                n_r_nodes_v.append(node)  # 写入子节点node
            # material节点处理
            r_material_v = elem.find('geometry').find('primitiveGroup').find('material')  # 找出原文件的material节点
            n_renderSet_v.append(r_material_v)  # 写入renderSet节点

        # 处理lods节点
        n_lod_v = ET.SubElement(n_lods_v, 'lod')
        extent_v = ET.SubElement(n_lod_v, 'extent')
        castsShadow_v = ET.SubElement(n_lod_v, 'castsShadow')
        renderSets_v = ET.SubElement(n_lod_v, 'renderSets')

        # extent节点
        extent_v.text = '2000'  # <extent> 2000 </extent>
        # castsShadow节点
        castsShadow_v.text = 'true'  # <castShadow> true </castShadow>
        # renderSets节点
        num_lod = i
        while i:
            renderSet_v = ET.SubElement(renderSets_v, 'renderSet')
            renderSet_v.text = name_v[num_lod - i]
            i = i - 1

        # print('finish', '\n')

        # 生成新的visual文件
        visual_str = prettify(n_root_v)
        # 去除版本声明
        visual_str = '\n'.join([
            line for line in visual_str.split('\n')
            if line.strip() != '<?xml version="1.0" ?>'
        ])
        # 去除空白行
        visual_str = '\n'.join([
            line for line in visual_str.split('\n')
            if line.strip() != ''
        ])
        f = open(FileAdderss_v, 'w', encoding='utf-8')
        f.write(visual_str)
        f.close()
        print(f'[Visual Fix]{path} \n修复完成!')     
    return 0
