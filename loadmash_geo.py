#####################################################################
# imports
from ctypes import c_long
from struct import unpack,pack
# from mathutils import Vector
# from .loaddatamesh import UnpackNormal
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

        '''
        self.indices_section_name = primitive_name #Indices group name
        self.vertices_section_name = vertices_name #Vertices group name
        header = unpack('<I', self.__pfile.read(4))[0] #First 4 bytes of the file
        assert(header == 0x42a14e65) #Check if it is a real .primitives file i.e. first four bytes are B¡Ne
        self.__load_packed_section() #Read the table section of the .primitives file and lists length+position of all sections
        self.__load_XYZNUV(
            self.__PackedGroups[primitive_name]['position'],
            self.__PackedGroups[vertices_name]['position']
            ) #loads the vertex and triangle data from the locations
        '''
        self.__pfile.close() #Close .geometry file

    def load_header_section(self):
        # 读取文件头存储的各模型数量
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

        VertexInfo, IndexInfo = self.load_BlocInfo(VertexInfoOffset, VertexBlocNum, IndexInfoOffset, IndexBlocNum)
        
        if self.__debug:
            print("Vertex Info List:", VertexInfo)
            print("Index Info List:", IndexInfo)

        # 加载顶点信息和面信息 (编码似乎经过压缩, 需要解码)
        # Vertices = self.load_VertexData(VertexInfo, VertexDataOffset, VertexTypeNum, VertexBlocNum)
        # Indices = self.load_IndexData(IndexInfo, IndexDataOffset, IndexTypeNum, IndexBlocNum)

        self.load_ArmorData(ArmorDataOffset, ArmorBlocNum)
        # self.load_CollisionData(CollisDataOffset, CollissionBlocNum)

    def load_BlocInfo(self, VertexInfoOffset, VertexBlocNum, IndexInfoOffset, IndexBlocNum):
        self.__pfile.seek(VertexInfoOffset)
        # Read vertex block info here
        Num = 0
        VertexInfo = []
        while Num < VertexBlocNum:
            # Read each vertex block info
            Vertex_bloc_name = str(hex(unpack('<I', self.__pfile.read(4))[0])) #Block name
            Vertex_bloc_format = unpack('<H', self.__pfile.read(2))[0] # Block format
            Vertex_bloc_paring = unpack('<H', self.__pfile.read(2))[0] # Block format
            Vertex_bloc_offset = unpack('<I', self.__pfile.read(4))[0] # Offset to vertex data
            Vertex_bloc_count = unpack('<I', self.__pfile.read(4))[0] # Number of vertices
            if self.__debug:
                print('[GeoUnpcak] Vertex[{}]:'.format(Num))
                print("Vertex Block Name:{};Format:{};Paring:{};Offset:{};Count:{}\n".format(
                    Vertex_bloc_name, Vertex_bloc_format, Vertex_bloc_paring, Vertex_bloc_offset, Vertex_bloc_count
                    ))
                VertexInfo.append({
                    'name': Vertex_bloc_name,
                    'format': Vertex_bloc_format,
                    'paring': Vertex_bloc_paring,
                    'offset': Vertex_bloc_offset,
                    'count': Vertex_bloc_count
                    })
            Num += 1
        self.__pfile.seek(IndexInfoOffset)
        # Read index block info here
        Num = 0
        IndexInfo = []
        while Num < IndexBlocNum:
            # Read each index block info
            Index_bloc_name = str(hex(unpack('<I', self.__pfile.read(4))[0])) # Block name
            Index_bloc_format = unpack('<H', self.__pfile.read(2))[0] # Block format
            Index_bloc_paring = unpack('<H', self.__pfile.read(2))[0] # Block format
            Index_bloc_offset = unpack('<I', self.__pfile.read(4))[0] # Offset to index data
            Index_bloc_count = unpack('<I', self.__pfile.read(4))[0] # Number of index
            if self.__debug:
                print('[GeoUnpcak] Index[{}]:'.format(Num))
                print("Index Block Name:{};Format:{};Paring:{};Offset:{};Count:{}\n".format(
                    Index_bloc_name, Index_bloc_format, Index_bloc_paring, Index_bloc_offset, Index_bloc_count
                    ))
            IndexInfo.append({
                'name': Index_bloc_name,
                'format': Index_bloc_format,
                'paring': Index_bloc_paring,
                'offset': Index_bloc_offset,
                'count': Index_bloc_count
            })
            Num += 1
        return VertexInfo, IndexInfo
    
    def load_VertexData(self, Vertex_Info, VertexDataOffset, VertexTypeNum, VertexBlocNum):
        TypeCount = 0
        Vertices = []
        LargeVertexInfo = []

        while TypeCount < VertexTypeNum:
            self.__pfile.seek(VertexDataOffset+32*TypeCount) # Go to vertex data offset
            LargeVertexDataOffset = unpack('<I', self.__pfile.read(4))[0] # LargeVertexDataOffset + VertexDataOffset -> 实际偏移量
            self.__pfile.read(4) #skip 4 bytes
            LargeVertexTypeLength = unpack('<I', self.__pfile.read(4))[0]
            self.__pfile.read(4) #skip 4 bytes
            LargeVertexTypeOffset = unpack('<I', self.__pfile.read(4))[0]
            self.__pfile.read(4) #skip 4 bytes
            LargeVertexDataLength = unpack('<I', self.__pfile.read(4))[0] # 该组顶点数据总字节长
            SingleVertexSize = unpack('<H', self.__pfile.read(2))[0] # 单个顶点的字节长
            EndFlag = unpack('x?', self.__pfile.read(2))[0]

            self.__pfile.seek(VertexDataOffset+32*TypeCount+8+LargeVertexTypeOffset) # Go to vertex type string
            VertexTypeStr = self.__pfile.read(LargeVertexTypeLength).decode('utf-8').rstrip('\x00') # Vertex Type String

            if self.__debug:
                print('[GeoUnpcak] Vertex Data Type[{}]:'.format(TypeCount))
                print("Large Vertex Data Offset:{};Large Vertex Type Length:{};Large Vertex Type Offset:{};Large Vertex Data Length:{};Single Vertex Size:{};End Flag:{};Type String:{}\n".format(
                    LargeVertexDataOffset, LargeVertexTypeLength, LargeVertexTypeOffset, LargeVertexDataLength, SingleVertexSize, EndFlag, VertexTypeStr
                    ))
                
            LargeVertexInfo.append({
                    'LargeVertexDataOffset': LargeVertexDataOffset,
                    'LargeVertexTypeLength': LargeVertexTypeLength,
                    'LargeVertexTypeOffset': LargeVertexTypeOffset,
                    'LargeVertexDataLength': LargeVertexDataLength,
                    'SingleVertexSize': SingleVertexSize,
                    'VertexTypeStr': VertexTypeStr,
                    'EndFlag': EndFlag
                    })
            TypeCount += 1
        
        # 解析各类型顶点数据
        VerticesCount = 0
        while VerticesCount < VertexBlocNum:
            VertexBlocOffset = Vertex_Info[VerticesCount]['offset']*LargeVertexInfo[Vertex_Info[VerticesCount]['format']]['SingleVertexSize'] \
                                + LargeVertexInfo[Vertex_Info[VerticesCount]['format']]['LargeVertexDataOffset'] + VertexDataOffset + 32*Vertex_Info[VerticesCount]['format'] + 8
            if self.__debug:
                print('[GeoUnpcak] Loading Vertex Bloc[{}] at offset:{} with format:{} (Type String:{}).'.format(
                    VerticesCount, VertexBlocOffset, Vertex_Info[VerticesCount]['format'],
                    LargeVertexInfo[Vertex_Info[VerticesCount]['format']]['VertexTypeStr']
                    ))
            if LargeVertexInfo[Vertex_Info[VerticesCount]['format']]['VertexTypeStr'] == "set3/xyznuvpc":
                self.__pfile.seek(VertexBlocOffset)
                Num = 0
                Vertex = []
                while Num < Vertex_Info[VerticesCount]['count']:
                    # Read each vertex data
                    vx = unpack('<f', self.__pfile.read(4))[0]
                    vz = unpack('<f', self.__pfile.read(4))[0]
                    vy = unpack('<f', self.__pfile.read(4))[0]
                    packed_n = unpack('<I', self.__pfile.read(4))[0]
                    u = 0.5 + unpack('<e', self.__pfile.read(2))[0]
                    v = 0.5 - unpack('<e', self.__pfile.read(2))[0]
                    
                    nx, ny, nz = UnpackNormal(packed_n)

                    Vertex.append({
                        'co' : (vx, vy, vz),
                        'normal' : (nx, ny, nz),
                        'uv' : (u, v)})

                    Num += 1
            elif LargeVertexInfo[Vertex_Info[VerticesCount]['format']]['VertexTypeStr'] == "set3/xyznuvtbpc":
                self.__pfile.seek(VertexBlocOffset)
                Num = 0
                Vertex = []
                while Num < Vertex_Info[VerticesCount]['count']:
                    # Read each vertex data
                    vx = unpack('<f', self.__pfile.read(4))[0]
                    vz = unpack('<f', self.__pfile.read(4))[0]
                    vy = unpack('<f', self.__pfile.read(4))[0]
                    packed_n = unpack('<I', self.__pfile.read(4))[0]
                    u = 0.5 + unpack('<e', self.__pfile.read(2))[0]
                    v = 0.5 - unpack('<e', self.__pfile.read(2))[0]
                    packed_tangent = unpack('<I', self.__pfile.read(4))[0]
                    packed_binormal = unpack('<I', self.__pfile.read(4))[0]

                    tx,ty,tz = UnpackNormal(packed_tangent)
                    bx,by,bz = UnpackNormal(packed_binormal)
                    nx, ny, nz = UnpackNormal(packed_n)

                    Vertex.append({
                        'co' : (vx, vy, vz),
                        'normal' : (nx, ny, nz),
                        'uv' : (u, v),
                        'tangent' : (tx, ty, tz),
                        'binormal' : (bx, by, bz)})

                    Num += 1
            elif LargeVertexInfo[Vertex_Info[VerticesCount]['format']]['VertexTypeStr'] == "set3/xyznuvrpc":
                self.__pfile.seek(VertexBlocOffset)
                Num = 0
                Vertex = []
                while Num < Vertex_Info[VerticesCount]['count']:
                    # Read each vertex data
                    vx = unpack('<f', self.__pfile.read(4))[0]
                    vz = unpack('<f', self.__pfile.read(4))[0]
                    vy = unpack('<f', self.__pfile.read(4))[0]
                    packed_n = unpack('<I', self.__pfile.read(4))[0]
                    u = 0.5 + unpack('<e', self.__pfile.read(2))[0]
                    v = 0.5 - unpack('<e', self.__pfile.read(2))[0]
                    r = unpack('<f', self.__pfile.read(4))[0]

                    nx, ny, nz = UnpackNormal(packed_n)

                    Vertex.append({
                        'co' : (vx, vy, vz),
                        'normal' : (nx, ny, nz),
                        'uv' : (u, v),
                        'radius' : r})

                    Num += 1
            else:
                if self.__debug:
                    print("[GeoUnpcak] Unknown Vertex Type String:", LargeVertexInfo[Vertex_Info[VerticesCount]['format']]['VertexTypeStr'])

            Vertices.append({
                        'name' : Vertex_Info[VerticesCount]['name'],
                        'paring' : Vertex_Info[VerticesCount]['paring'],
                        'Vertex' : Vertex
                    })
            VerticesCount += 1
            if self.__debug:
                print('[GeoUnpcak] Loaded Vertex Bloc[{}] with {} vertices.\n'.format(VerticesCount-1, Vertex_Info[VerticesCount-1]['count']))
                #print("Vertices Data:", Vertex)
        return Vertices
    
    def load_IndexData(self, Index_Info, IndexDataOffset, IndexTypeNum, IndexBlocNum):
        Indices = []
        
        return Indices
    
    def load_CollisionData(self, CollisDataOffset, CollissionBlocNum):
        Collisions = []
        if CollissionBlocNum > 0:
            self.__pfile.seek(CollisDataOffset)
            # Read collision data here

            # 32 bytes of collision header
            CollisBlocLength = unpack('<I', self.__pfile.read(4))[0]
            self.__pfile.read(4) #skip 4 bytes
            CollisNameLength = unpack('<I', self.__pfile.read(4))[0]
            self.__pfile.read(4) #skip 4 bytes
            CollisNameOffset = unpack('<I', self.__pfile.read(4))[0]
            self.__pfile.read(4) #skip 4 bytes
            CollisDataLength = unpack('<I', self.__pfile.read(4))[0]
            self.__pfile.read(4) #skip 4 bytes

            # self.geo_collis2pri(CollisDataOffset, CollisBlocLength, CollisNameLength, CollisNameOffset) # 将collision数据转换为primitive文件

        return Collisions
    
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

            if False:
                PiecesNum = 0
                ArmorPieces = []
                zuobiao = []
                f = open("./Reference/armor_CM_PA_united.armor.txt", "a", encoding='utf-8')
                while PiecesNum < ArmorPiecesNum:
                    Id = unpack('<I', self.__pfile.read(4))[0]
                    UnknownB = self.__pfile.read(24)
                    VertexIndicesNum = unpack('<I', self.__pfile.read(4))[0]
                    if self.__debug:
                        print('[GeoUnpcak]   Armor Piece[{}]: ID:{};UnknownB:{};Vertex Indices Num:{}\n'.format(
                            PiecesNum, Id, UnknownB, VertexIndicesNum
                        ))
                    VertexNum = 0
                    Vertex = []
                    while VertexNum < VertexIndicesNum:
                        vx = unpack('<f', self.__pfile.read(4))[0]
                        vz = unpack('<f', self.__pfile.read(4))[0]
                        vy = unpack('<f', self.__pfile.read(4))[0]
                        UnknownC = self.__pfile.read(4)
                        Vertex.append({
                            'co' : (vx, vy, vz),
                            'unknownC' : UnknownC
                        })
                        zuobiao.append((vx, vy, vz))
                        if self.__debug:
                            print('[GeoUnpcak]   Armor Piece[{}] Vertex[{}]: Co=({}, {}, {}), UnknownC={}'.format(
                                PiecesNum, VertexNum, vx, vy, vz, UnknownC
                            ))
                        f.write('{}, {}, {},{}\n'.format(
                                vx, vy, vz, UnknownC))
                        VertexNum += 1
                    ArmorPieces.append({
                        'id' : Id,
                        'unknownB' : UnknownB,
                        'vertices' : Vertex
                    })
                    PiecesNum += 1

                NameOffset = ArmorNameOffset + ArmorDataOffset + 8
                self.__pfile.seek(NameOffset)
                ArmorName = unpack('<{}s'.format(ArmorNameLength), self.__pfile.read(ArmorNameLength))[0].decode('utf-8').rstrip('\x00')
                if self.__debug:
                    print('[GeoUnpcak]   Armor Name at offset {}: {}'.format(
                        NameOffset, ArmorName
                    ))

                Armors.append({
                    'name' : ArmorName,
                    'unknownA' : UnknownA,
                    'armor_pieces' : ArmorPieces
                })
            
            # 将armor数据转换为primitive文件
            self.geo_armors2pri(ArmorDataOffset, ArmorBlocLength, ArmorNameLength, ArmorNameOffset) 
        return Armors
    
    def geo_armors2pri(self, ArmorDataOffset, ArmorBlocLength, ArmorNameLength, ArmorNameOffset):
        # 将geo文件中的armor提取出来并转换为primitive文件。
        # Filename = "ASC303_Hawaii_1955_armor.primitives"

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
    
    def geo_collis2pri(self, CollisDataOffset, CollisBlocLength, CollisNameLength, CollisNameOffset):
        # 将geo文件中的collission提取出来并转换为primitive文件(但疑似并没有效果,无法再正常合并到geo文件中,可能需要考虑其他方式)。
        # Filename = "ASC303_Hawaii_1955_collision.primitives"

        Filename = os.path.splitext(os.path.basename(self.__pfile.name))[0] + "_collision.primitives"

        self.__pfile.seek(CollisDataOffset + 32) # Skip collision block header
        CollisData = self.__pfile.read(CollisBlocLength)  # Read collision data
        f = open(os.path.dirname(self.__pfile.name) + Filename, "wb")
        
        Data_Length = pack('<QQL', len(CollisData), 0, 0) # 20 bytes for data length

        self.__pfile.seek(CollisNameOffset+ CollisDataOffset + 8) # Go to collision name offset
        CollisName = unpack('<{}s'.format(CollisNameLength), self.__pfile.read(CollisNameLength))[0].decode('utf-8').rstrip('\x00') # Collision name string
        Name_Length = pack('<L', len(CollisName)) # 4 bytes for name length
        Name_str = CollisName.encode('utf-8') + (4-len(CollisName)%4)*b'\x00' # Name string in bytes, padded to 4 bytes
        info_Length = pack('<L',len(Data_Length + Name_Length + Name_str)) # 20 bytes for info length (not used here)

        Pri_data = b'\x65\x4e\xa1\x42' + CollisData + Data_Length + Name_Length + Name_str + info_Length # B¡Ne + collision data + data length + name length + name string + info length
        f.write(Pri_data)
        f.close()
        print('[GeoUnpcak] Collision data has been converted to primitive file: {}'.format(Filename))

        return 0

if __name__ == "__main__":

    '''
    总之现在可以读取armor数据并且转换成pri了,虽然不是本来的目的,也没有GUI,凑合用吧
    '''

    # 在这里填geo路径(最好是绝对路径了),然后运行,会在同目录下生成一个同名+armor的pri文件,里面是从geo里提取出来的armor数据(如果有的话),可以用来合并回geo文件中。
    filepath = "./Reference/AGM127_5in54_Mark42.geometry"
    
    loadgeo = LoadGeoData2Mesh(filepath, True)