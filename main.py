import traceback

############## GLOBAL CONSTANTS

DISC_PATH = "disc"

NAME_CLUSTER = "xxx SIMPLE FAT FILE SYSTEM SIMULATION xxx size 3000 xx clusters 30 xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"

NAME_CLUSTER_START = 100
TABLE_CLUSTER_START = 101
ROOT_CLUSTER_START = 102


DISC_FULL_ERROR = -1
FILE_TABLE_FULL_ERROR = -2

############## CLASSES

class colors:
    WARNING = '\033[95m'
    INFO_4 = '\033[96m'
    INFO_2 = '\033[36m'
    INFO_3 = '\033[94m'
    OK = '\033[92m'
    INFO_1 = '\033[93m'
    ERROR = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class FileHandle():
    def __init__(self, name = None, size = None, position = None, origin = None):
        self.name = name
        self.size = size
        self.position = position
        self.origin = origin

############## FUNCTIONS
        
def print_color_wrapper(text, format):
    print(format + text + colors.END)

def write_disc(disc:bytes):
    with open(DISC_PATH, 'wb') as f:
        f.write(disc)

def read_disc():
    with open(DISC_PATH, "rb") as f:
        return f.read()

def create_disc_with_size(size_in_bytes: int):
    with open(DISC_PATH, 'wb') as f:
        f.write(b'\0' * size_in_bytes)

def format_disc():
    disc = read_disc()
    byte_array = bytearray(disc)
    for i, char in enumerate(NAME_CLUSTER):
        byte_array[i] = ord(char)
    
    # set cluster 0 as not free
    byte_array[NAME_CLUSTER_START] = 255
    # set cluster 1 as not free
    byte_array[TABLE_CLUSTER_START] = 255
    # set cluster 2 as not free
    byte_array[ROOT_CLUSTER_START] = 255
    write_disc(bytes(byte_array))
    return byte_array

def mount_disc():
    try:
        disc = read_disc()
        return disc
    except Exception:
        traceback.print_exc()
        print_color_wrapper("Disc mount error", colors.ERROR)
        print_color_wrapper("Creating new disc", colors.OK)
        create_disc_with_size(3072)
        print_color_wrapper("Formating disc", colors.OK)
        byte_array = format_disc()
        return bytes(byte_array)

def unmount_disc():
    try:
        disc = read_disc()
        write_disc(disc)
        del disc
        print_color_wrapper("Disc successfully unmounted", colors.OK)
        return True
    except Exception:
        traceback.print_exc()
        return False

def open_file(filename: str):
    fh = None
    try:
        if len(filename) == 1:
            if isinstance(filename, str):
                disc = read_disc()
                byte_array = bytearray(disc)
                fh = set_file_handle(byte_array, filename)
            else:
                raise ValueError(colors.ERROR + "Wrong filename. Filename type must be str" + colors.END)
        else:
            raise ValueError(colors.ERROR + "Wrong filename. Filename length must be 1" + colors.END)
        return fh
    except Exception:
        traceback.print_exc()
        return fh

def file_table_write_new_file(byte_array):
    retval = None
    if byte_array[199] != 0:
        retval = FILE_TABLE_FULL_ERROR
    index = 101
    # If there is space in file table
    if retval == None:
        while True:
            if index == 130:
                retval = DISC_FULL_ERROR
                break
            if byte_array[index] == 0:
                byte_array[index] = 255
                retval = index
                break
            index += 1
        print_color_wrapper("Writing new file to the file table index: " + str(index), colors.OK)
        write_disc(bytes(byte_array))
    return retval

def file_table_extend_file(byte_array, previous_index):
    retval = None
    try:
        if byte_array[199] != 0:
            retval = FILE_TABLE_FULL_ERROR
            raise MemoryError(colors.ERROR + "File table full" + colors.END) 
        index = 101
        # If there is space in file table
        if retval == None:
            while True:
                if index == 130:
                    retval = DISC_FULL_ERROR
                    raise MemoryError(colors.ERROR + "Disc full" + colors.END) 
                if byte_array[index] == 0:
                    byte_array[index] = 255
                    byte_array[previous_index] = index
                    retval = index
                    break
                index += 1
            print_color_wrapper("Extending file to the file table index: " + str(index), colors.WARNING)
            write_disc(bytes(byte_array))
        return retval
    except Exception:
        traceback.print_exc()
        return retval

def root_cluster_write_new_file(filename, byte_array, root_index, file_cluster):
    try:
        print_color_wrapper("Writing new file to the root cluster index: " + str(root_index), colors.OK)
        fh = FileHandle()

        # set origin
        fh.origin = root_index

        # set filename
        byte_array[root_index] = ord(filename)
        fh.name = filename

        # set position
        root_index += 1
        byte_array[root_index] = file_cluster
        fh.position = byte_array[root_index]

        # set size
        root_index += 1
        byte_array[root_index] = 1
        fh.size = 1

        write_disc(bytes(byte_array))
        return fh
    except Exception:
        traceback.print_exc()
        return None
    
def set_file_handle(byte_array, filename):
    # start of root cluster
    retval = None
    try:
        root_index = find_root_cluster(byte_array, ROOT_CLUSTER_START)
        root_index = (root_index % 100) * 100
        print_color_wrapper("Root cluster start index is: " + str(root_index),colors.INFO_3)
        root_cluster_end = root_index + 99
        if check_root_cluster_write_space(byte_array, root_cluster_end):
            while(True):
                # if root cluster index is empty start writing
                if byte_array[root_index] == 0:
                    retval = file_table_write_new_file(byte_array)
                    if retval == FILE_TABLE_FULL_ERROR: 
                        raise MemoryError(colors.ERROR + "File table full" + colors.END) 
                    elif retval == DISC_FULL_ERROR: 
                        raise MemoryError(colors.ERROR + "Disc full" + colors.END)
                    elif retval != None:
                        file_table_cluster = retval
                    retval = root_cluster_write_new_file(filename, byte_array, root_index, file_table_cluster)
                    break
                else:
                    root_index += 1
        else:
            retval = DISC_FULL_ERROR
        return retval
    except Exception:
        traceback.print_exc()
        return retval

def find_root_cluster(byte_array, index):
    if byte_array[index] == 255:
        return index
    else:
        index = find_root_cluster(byte_array, index)
        return index

def check_root_cluster_write_space(byte_array, index):
    if byte_array[index] == 0 and byte_array[index-1] and byte_array[index-2]:
        return True
    else:
        return DISC_FULL_ERROR

def print_clusters(cluster_num):

    disc = read_disc()
    int_array = [int(byte) for byte in disc] 
    start_index = 100
    print_color_wrapper("########## FIRST CLUSTER ############", colors.INFO_1)
    print(disc[:start_index])
    print_color_wrapper("########## FILE TABLE CLUSTER #######", colors.INFO_1)
    print(int_array[start_index:start_index+100])
    start_index += 100
    print_color_wrapper("########## ROOT CLUSTER #############", colors.INFO_1)
    print(int_array[start_index:start_index+100])
    start_index += 100

    for i in range(cluster_num):
        print_color_wrapper("########## FILE CLUSTER %s ###########"%(i+1), colors.INFO_2)
        print(disc[start_index:start_index + 100])
        start_index += 100
    
def write_file(fh, buffer):
    disc = read_disc()
    byte_array = bytearray(disc)
    cluster_index = (fh.position % 100) * 100
    starting_index = cluster_index
    while True:
        if byte_array[cluster_index] == 0:
            cnt = 0
            for i in buffer:
                index = cluster_index + cnt
                if index > starting_index + 99:
                    retval = file_table_extend_file(byte_array, fh.position)
                    if retval != DISC_FULL_ERROR and retval != FILE_TABLE_FULL_ERROR:
                        # set new cluster starting indices
                        cluster_index = (retval % 100) * 100
                        starting_index = cluster_index
                        cnt = 0
                        index = cluster_index + cnt

                        # increment file size
                        fh.size = fh.size + 1
                        byte_array[fh.origin + 2] = fh.size
                    else:
                        return retval
                byte_array[index] = ord(i)
                cnt += 1
            write_disc(bytes(byte_array))
            break
        cluster_index += 1

############## APPLICATION START

if __name__ == "__main__":

    disc = mount_disc()
    fh = open_file("t")
    if fh != DISC_FULL_ERROR and FILE_TABLE_FULL_ERROR:
        write_file(fh, "0123456789" * 21)
    print_clusters(2)
    #unmount_disc()
