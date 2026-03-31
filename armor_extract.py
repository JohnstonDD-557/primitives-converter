#####################################################################
# imports
from ctypes import c_long
from struct import unpack,pack
import os

#####################################################################
# Unpack normal from 4-byte int
def UnpackNormal(packed):
    pky = (packed>>22)&0x1FF
    pkz = (packed>>11)&0x3FF
    pkx = packed&0x3FF
    x = pkx/1023.0
    if pkx & (1<<10):
        x = -x
    y = pky/511.0
    if pky & (1<<9):
        y = -y
    z = pkz/1023.0
    if pkz & (1<<10):
        z = -z
    return (x, z, y)

#####################################################################
# loadgeomesh
# 无视visual文件,直接解析geo文件,并读取armor信息(unknownA,B&C尝试存入顶点和模型中)
# 和collission信息(可能需要直接存入模型中,数据结构未知)

class LoadGeoData2Mesh:
    PrimitiveGroups = None #List of groups for each set
    uv_list = None #UV sublist
    normal_list = None #Normal sublist
    tangent_list = None #Tangent sublist
    binormal_list = None #Binormal sublist
    bones_info = None #Bones sublist
    vertices = None #Vertices sublist
    indices = None #Indices sublist
    vertices_section_name = None #Name of the set + .vertices
    indices_section_name = None #Name of the set + .indices
    vertices_format = None #Format of this set
    __PackedGroups = None #Lists some redundant info
    __pfile = None #Primitive file
    __debug = False

    def __init__(self, filepath, extra_info):
        self.__debug = extra_info #Debug mode?
        self.__pfile = open(filepath, 'rb') #Open .geometry file
        self.load_header_section()
        self.__pfile.close() #Close .geometry file

    def load_header_section(self):
        # 读取文件头存储的各项信息
        VertexTypeNum = unpack('<I', self.__pfile.read(4))[0]
        IndexTypeNum = unpack('<I', self.__pfile.read(4))[0]
        VertexBlocNum = unpack('<I', self.__pfile.read(4))[0]
        IndexBlocNum = unpack('<I', self.__pfile.read(4))[0]
        CollissionBlocNum = unpack('<I', self.__pfile.read(4))[0]
        ArmorBlocNum = unpack('<I', self.__pfile.read(4))[0]
        VertexInfoOffset = unpack('<I', self.__pfile.read(4))[0]
        self.__pfile.read(4) #skip 4 bytes
        IndexInfoOffset = unpack('<I', self.__pfile.read(4))[0]
        self.__pfile.read(4) #skip 4 bytes
        VertexDataOffset = unpack('<I', self.__pfile.read(4))[0]
        self.__pfile.read(4) #skip 4 bytes
        IndexDataOffset = unpack('<I', self.__pfile.read(4))[0]
        self.__pfile.read(4) #skip 4 bytes
        CollisDataOffset = unpack('<I', self.__pfile.read(4))[0]
        self.__pfile.read(4) #skip 4 bytes
        ArmorDataOffset = unpack('<I', self.__pfile.read(4))[0]
        self.__pfile.read(4) #skip 4 bytes

        if self.__debug:
            print("Vertex Types:{};Index Types:{};Vertex Bloc:{};Index Bloc:{};Collision Bloc:{};Armor Bloc:{}".format(VertexTypeNum, IndexTypeNum, VertexBlocNum, IndexBlocNum, CollissionBlocNum, ArmorBlocNum))
            print("Vertex Info Offset:{};Index Info Offset:{};Vertex Data Offset:{};Index Data Offset:{};Collision Data Offset:{};Armor Data Offset:{}\n".format(
                VertexInfoOffset, IndexInfoOffset, VertexDataOffset, IndexDataOffset, CollisDataOffset, ArmorDataOffset
                ))

        self.load_ArmorData(ArmorDataOffset, ArmorBlocNum)

    def load_ArmorData(self, ArmorDataOffset, ArmorBlocNum):
        Armors = []
        if ArmorBlocNum > 0:
            self.__pfile.seek(ArmorDataOffset)

            # 32 bytes of armor block header
            ArmorBlocLength = unpack('<I', self.__pfile.read(4))[0]
            self.__pfile.read(4) #skip 4 bytes
            ArmorNameLength = unpack('<I', self.__pfile.read(4))[0]
            self.__pfile.read(4) #skip 4 bytes
            ArmorNameOffset = unpack('<I', self.__pfile.read(4))[0]
            self.__pfile.read(4) #skip 4 bytes
            ArmorPiecesLength = unpack('<I', self.__pfile.read(4))[0]
            self.__pfile.read(4) #skip 4 bytes
            

            ID = unpack('<I', self.__pfile.read(4))[0] # 01 00 00 80 for gun armor?
            UnknownA = self.__pfile.read(24)
            ArmorPiecesNum = unpack('<I', self.__pfile.read(4))[0]
            if self.__debug:
                print('[GeoUnpcak] Armor Data:')
                print("Armor Bloc Length:{};Armor Name Length:{};Armor Name Offset:{};UnknownA:{};Armor Pieces Num:{}\n".format(
                    ArmorBlocLength, ArmorNameLength, ArmorNameOffset, UnknownA, ArmorPiecesNum
                    ))

            
            # 将armor数据转换为primitive文件
            self.geo_armors2pri(ArmorDataOffset, ArmorBlocLength, ArmorNameLength, ArmorNameOffset) 

        return Armors
    
    def geo_armors2pri(self, ArmorDataOffset, ArmorBlocLength, ArmorNameLength, ArmorNameOffset):
        # 将geo文件中的armor提取出来并转换为primitive文件。

        Filename = os.path.splitext(os.path.basename(self.__pfile.name))[0] + "_armor.primitives"

        self.__pfile.seek(ArmorDataOffset + 32) # Skip armor block header
        ArmorData = self.__pfile.read(ArmorBlocLength)  # Read armor data
        f = open(os.path.dirname(self.__pfile.name) + '/' + Filename, "wb")
        # print(os.path.dirname(self.__pfile.name))
        Data_Length = pack('<QQL', len(ArmorData), 0, 0) # 20 bytes for data length

        self.__pfile.seek(ArmorNameOffset+ ArmorDataOffset + 8) # Go to armor name offset
        ArmorName = unpack('<{}s'.format(ArmorNameLength), self.__pfile.read(ArmorNameLength))[0].decode('utf-8').rstrip('\x00') # Armor name string
        Name_Length = pack('<L', len(ArmorName)) # 4 bytes for name length
        Name_str = ArmorName.encode('utf-8') + (4-len(ArmorName)%4)*b'\x00' # Name string in bytes, padded to 4 bytes
        info_Length = pack('<L',len(Data_Length + Name_Length + Name_str)) # 20 bytes for info length (not used here)

        Pri_data = b'\x65\x4e\xa1\x42' + ArmorData + Data_Length + Name_Length + Name_str + info_Length # B¡Ne + armor data + data length + name length + name string + info length
        f.write(Pri_data)
        f.close()
        print('[GeoUnpcak] Armor data has been converted to primitive file: {}'.format(Filename))

        return 0

if __name__ == "__main__":

    '''
    总之现在可以读取armor数据并且转换成pri了,虽然不是本来的目的,也没有GUI,凑合用吧
    '''

    # 在这里填geo路径(最好是绝对路径了),然后运行,会在同目录下生成一个同名+armor的pri文件,里面是从geo里提取出来的armor数据(如果有的话),可以用来合并回geo文件中。
    filepath = "I:/Code/primitives-converter/Reference/AGM127_5in54_Mark42.geometry"
    
    loadgeo = LoadGeoData2Mesh(filepath, False)