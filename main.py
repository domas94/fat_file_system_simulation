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
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    INFO_2 = '\033[36m'
    INFO_3 = '\033[94m'
    OK = '\033[92m'
    INFO_1 = '\033[93m'
    ERROR = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class FileHandle():
    def __init__(self, filename = None, file_size = None, file_position = None):
        self.filename = filename
        self.file_size = file_size
        self.file_position = file_position

############## FUNCTIONS
        
def print_color_wrapper(text, format):
    print(format + text + colors.END)

def disc_write(disc:bytes):
    with open(DISC_PATH, 'wb') as f:
        f.write(disc)

def read_disc():
    with open(DISC_PATH, "rb") as f:
        return f.read()

def create_disc_with_size(size_in_bytes):
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
    disc_write(bytes(byte_array))
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
        disc_write(disc)
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
        disc_write(bytes(byte_array))
    return retval

def root_cluster_write_new_file(filename, byte_array, root_index, file_cluster):
    try:
        print_color_wrapper("Writing new file to the root cluster: " + str(root_index), colors.OK)
        fh = FileHandle()

        # set filename
        byte_array[root_index] = ord(filename)
        fh.filename = filename

        # set position
        root_index += 1
        byte_array[root_index] = file_cluster
        fh.file_position = byte_array[root_index]

        # set size
        root_index += 1
        byte_array[root_index] = 1
        fh.file_size = 1

        disc_write(bytes(byte_array))
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
        print_color_wrapper("Root cluster index is: " + str(root_index),colors.INFO_3)
        root_cluster_end = root_index + 99
        if check_root_cluster_write_space(byte_array, root_cluster_end):
            while(True):
                # if root cluster index is empty start writing
                if byte_array[root_index] == 0:
                    retval = file_table_write_new_file(byte_array)
                    if retval == FILE_TABLE_FULL_ERROR: 
                        raise MemoryError(colors.ERROR + "File table full" + colors.END) 
                    elif retval == DISC_FULL_ERROR: 
                        raise MemoryError(colors.ERROR + "Disc table full" + colors.END)
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

def print_clusters(disc, clusters):

    start_index = 100
    print_color_wrapper("########## FIRST CLUSTER ############", colors.INFO_1)
    print(disc[:start_index])
    print_color_wrapper("########## FILE TABLE CLUSTER #######", colors.INFO_1)
    print(disc[start_index:start_index+100])
    start_index += 100
    print_color_wrapper("########## ROOT CLUSTER #############", colors.INFO_1)
    print(disc[start_index:start_index+100])
    start_index += 100

    for i in range(clusters):
        print_color_wrapper("########## FILE CLUSTER %s ###########"%(i+1), colors.INFO_2)
        print(disc[start_index:start_index + 100])
        start_index += 100

############## APPLICATION START

if __name__ == "__main__":

    disc = mount_disc()
    fh = open_file("f")
    disc = read_disc()
    print_clusters(disc, 1)
    unmount_disc()
