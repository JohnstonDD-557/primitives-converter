#! /usr/bin/env python3
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

将World of Warships的新版本(14.1+)visual文件转换为旧版本(13.8)

'''

# __DEBUG__参数说明: 默认为True
# True:生成为.fix文件,不覆盖源文件
# False:直接生成为.visual文件,覆盖源文件
__DEBUG__ = True

# ShapeClear 参数说明:  默认为False
# 注:该功能未经过详细测试,使用时上方DEBUG最好为True;若节点命名中含有Shape,此功能无法正常运行
# True:自动清理renderSet.nodes.node中多出来的Shape字段
# False:不进行清理
ShapeClear = False

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


def Visual_new2old(file_path):
    p1 = r"(PnFMods/[^/]*/[^/]*/)"          # PnFMods/***/***/
    p2 = r"(./[^\\]*\\)"                    # ./***\
    p3 = r"(PnFMods/[^/]*/[^/]*/[^/]*/)"    # PnFMods/***/***/***/
    
    if file_path:
        fileObj_v = file_path  # 不影响原变量
        i = 0  # render节点数目记录 用于后续lod节点写入
        name_v = []  # name节点所对应的值
        flag_old = 1  # 是否为新版本model

        # 读取visual文件内容,以确认是否为新版本model文件
        xmlstring = fileObj_v
        tree_v = ET.parse(xmlstring)
        root_v = tree_v.getroot()

        # 检测是否为旧版本visual文件
        # 当前检测原理:检测内部是否有 新版本版本含有的skeleton节点
        for elem in root_v.iter('skeleton'):
            flag_old = 0

        if not flag_old:
            # 建立生成的visual文件基础
            o_root_v = ET.Element(root_v.tag)  # 创建需生成的visual文件的根节点

            # 读取visual文件的node数据  后续层级均相同且新文件中无需重复
            o_node_v = root_v.find('skeleton').find('node')
            o_root_v.append(o_node_v)   # 写入node节点的数据

            # 在lod节点中找到对应所需的renderSet
            lod_v = root_v.find('lods').find('lod').find('renderSets')
            for elem in lod_v.iter('renderSet'):
                name_v.append(elem.text)
                # 清理干扰判断的字符 (空格 缩进 换行)
                name_v[i] = re.sub(' ', '', name_v[i])
                name_v[i] = re.sub('\t', '', name_v[i])
                name_v[i] = re.sub('\n', '', name_v[i])
                i = i + 1

            # 处理renderSets节点
            i = i - 1
            renderSets_v = root_v.find('renderSets')    # 将renderSets中的对应节点搬出来 这里可能会搬出来很多一样的节点 or 丢掉很多节点也说不定
            for elem in renderSets_v.iter('renderSet'):
                # 检测是否为所需renderSet节点
                # 读取name节点
                n_name_v = elem.find('name').text
                # 清理干扰判断的字符 (空格 缩进 换行)
                n_name_v = re.sub(' ', '', n_name_v)
                n_name_v = re.sub('\t', '', n_name_v)
                n_name_v = re.sub('\n', '', n_name_v)
                if n_name_v == name_v[i]:
                    # 处理该renderSet节点
                    o_renderSet_v = ET.SubElement(o_root_v, 'renderSet')    # 创建renderset节点

                    # treatAsWorldSpaceObject节点处理
                    n_treatAsWorldSpaceObject_v = elem.find('treatAsWorldSpaceObject')  # 找出原文件中对应节点
                    o_renderSet_v.append(n_treatAsWorldSpaceObject_v)  # 将子节点写入renderSet节点中
                        
                    # node节点处理
                    nodes = elem.find('nodes')
                    for elem_r in nodes.iter('node'):
                        o_node_v = ET.SubElement(o_renderSet_v, 'node')
                        o_node_v.text = elem_r.text

                    # geometry节点处理
                    o_geometry_v = ET.SubElement(o_renderSet_v, 'geometry')

                    # vertices与primitive节点
                    o_vertices_v = ET.SubElement(o_geometry_v, 'vertices')  # 建立vertices节点
                    o_primitive_v = ET.SubElement(o_geometry_v, 'primitive')    # 建立primitive节点
                    vertices_v = name_v[i] + '.vertices'
                    indices_v = name_v[i] + '.indices'
                    o_vertices_v.text = vertices_v
                    o_primitive_v.text = indices_v

                    # primitiveGroup节点
                    o_primitiveGroup_v = ET.SubElement(o_geometry_v, 'primitiveGroup')
                    o_primitiveGroup_v.text = '0'
                    n_materal_v = elem.find('material')
                    o_primitiveGroup_v.append(n_materal_v)
                    i = i - 1

            # 处理boundingBox节点
            n_boundingBox_v = ET.SubElement(o_root_v, 'boundingBox')  # 创建子节点 boundingBox
            min_v = root_v.find('boundingBox').find('min')
            max_v = root_v.find('boundingBox').find('max')
            n_boundingBox_v.append(min_v)
            n_boundingBox_v.append(max_v)

            # 生成新的visual文件
            visual_str = prettify(o_root_v)
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

            return visual_str
    return None

