"""Read PE string resources as data; never load or execute the CADe_SIMU binary."""
import argparse,hashlib,json,struct
from pathlib import Path

def resources(path):
    data=Path(path).read_bytes()
    u16=lambda p:struct.unpack_from('<H',data,p)[0]
    u32=lambda p:struct.unpack_from('<I',data,p)[0]
    pe=u32(0x3c)
    if data[:2]!=b'MZ' or data[pe:pe+4]!=b'PE\0\0':raise ValueError('Not a PE executable')
    optional=pe+24;sections=optional+u16(pe+20)
    def offset(rva):
        for i in range(u16(pe+6)):
            pos=sections+i*40
            size,address,raw_size,raw=struct.unpack_from('<IIII',data,pos+8)
            if address<=rva<address+max(size,raw_size):return raw+rva-address
        raise ValueError('Invalid resource RVA')
    root=offset(u32(optional+(112 if u16(optional)==0x20b else 96)+16))
    def entries(relative):
        pos=root+relative
        for i in range(u16(pos+12)+u16(pos+14)):
            yield struct.unpack_from('<II',data,pos+16+i*8)
    for kind,types in entries(0):
        for block,blocks in entries(types&0x7fffffff):
            for language,item in entries(blocks&0x7fffffff):
                rva,size=struct.unpack_from('<II',data,root+item);pos=offset(rva)
                yield kind,block,language,data[pos:pos+size]

def strings(path):
    result=[]
    for kind,block,language,data in resources(path):
        if kind!=6:continue
        pos=0
        for index in range(16):
            length=struct.unpack_from('<H',data,pos)[0];pos+=2
            value=data[pos:pos+length*2].decode('utf-16le');pos+=length*2
            if value:result.append(dict(id=(block-1)*16+index,language=language,text=value))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('executable');parser.add_argument('--output',required=True)
    args=parser.parse_args();source=Path(args.executable)
    result=dict(source_name=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest(),strings=strings(source))
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Read',len(result['strings']),'string resources without executing the binary')
