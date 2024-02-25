import traceback
import os
import sys

############## GLOBALS ##############

############## CONSTANTS

DISC_PATH = "disc"

NAME_CLUSTER = "xxx SIMPLE FAT FILE SYSTEM SIMULATION xxx size 3000 xx clusters 30 xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"

NAME_CLUSTER_START = 100
TABLE_CLUSTER_START = 101
ROOT_CLUSTER_START = 102
MAX_DISC_SIZE = 3000
CLUSTER_SIZE = 99

############## VARIABLES

############## ERRORS

DISC_FULL_ERROR = -1
FILE_TABLE_FULL_ERROR = -2

############## CLASSES ##############

""" Escape codes for colored print logs. """
class colors:
    INFO_PURPLE = '\033[95m'
    INFO_CYAN = '\033[96m'
    INFO_DARK_CYAN = '\033[36m'
    INFO_BLUE = '\033[94m'
    OK_GREEN = '\033[92m'
    INFO_YELLOW = '\033[93m'
    INFO_ORANGE = '\033[38;2;255;165;0m'
    ERROR_RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

""" Used for manipulation with files. """
class FileHandle():
    def __init__(self, name: str = None, size: int = None, position: int = None, origin: int = None, active_cluster: int = None):
        self.name = name
        self.size = size
        self.position = position
        self.origin = origin
        self.active_cluster = active_cluster

############## FUNCTIONS ##############

""" brief: Wrapper for print function. Used for colored text outputs. 
    param: text - string to be printed
    param: format - format and color specifier
    return: None """
def print_color_wrapper(text: str, format: str) -> None:
    print(format + text + colors.END)

""" Writes new data to the disc file. """
def write_disc(disc:bytes) -> None:
    with open(DISC_PATH, 'wb') as f:
        f.write(disc)

""" Reads disc data. """
def read_disc() -> None:
    with open(DISC_PATH, "rb") as f:
        return f.read()

""" Creates new disc with specified size. """
def create_disc_with_size(size_in_bytes: int) -> None:
    with open(DISC_PATH, 'wb') as f:
        f.write(b'\0' * size_in_bytes)

""" Formats clean disc data. """
def format_disc() -> bytearray:
    disc = read_disc()
    byte_array = bytearray(disc)
    for i, char in enumerate(NAME_CLUSTER):
        byte_array[i] = ord(char)
    
    # Set cluster 0 as occupied
    byte_array[NAME_CLUSTER_START] = 255
    # Set cluster 1 as occupied
    byte_array[TABLE_CLUSTER_START] = 255
    # Set cluster 2 as occupied
    byte_array[ROOT_CLUSTER_START] = 255
    write_disc(bytes(byte_array))
    return byte_array

""" Returns disc data as bytes. """
def mount_disc() -> bytes:
    try:
        disc = read_disc()
        return disc
    except Exception:
        traceback.print_exc()
        print_color_wrapper("Disc mount error", colors.ERROR_RED + colors.BOLD + colors.UNDERLINE)
        print_color_wrapper("Creating new disc", colors.BOLD + colors.INFO_PURPLE)
        create_disc_with_size(3072)
        print_color_wrapper("Formating disc", colors.BOLD + colors.INFO_PURPLE)
        byte_array = format_disc()
        return bytes(byte_array)

""" Removed name reference from memory. """
def unmount_disc() -> bool:
    try:
        disc = read_disc()
        write_disc(disc)
        # disc object memory address
        # print(id(disc))
        # disc object reference count
        # print(sys.getrefcount(disc))
        del disc
        print_color_wrapper("Removed disc object reference", colors.BOLD + colors.INFO_PURPLE)

        """ 
        id and getrefcount will now return UnboundLocalError since its name reference is deleted
        id(disc), sys.getrefcount(disc)
        When reference count drops to 0, Python's garbage collector will delete the object from the memory
        """
        return True
    except Exception:
        traceback.print_exc()
        return False

""" Creates new file. """
def open_file(filename: str) -> FileHandle:
    fh = None
    try:
        if len(filename) == 1:
            if isinstance(filename, str):
                disc = read_disc()
                byte_array = bytearray(disc)
                fh = set_file_handle(byte_array, filename)
            else:
                raise ValueError(colors.ERROR_RED + "Wrong filename. Filename type must be str" + colors.END)
        else:
            raise ValueError(colors.ERROR_RED + "Wrong filename. Filename length must be 1" + colors.END)
        return fh
    except Exception:
        traceback.print_exc()
        return fh

""" Writes new file data to the file table. """
def file_table_write_new_file(byte_array: bytearray, filename: str) -> int:
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
        print_color_wrapper("Writing new file %s to the file table index: " % filename + str(index), colors.OK_GREEN)
        write_disc(bytes(byte_array))
    return retval

""" Extends file to the next available cluster. """
def file_table_extend_file(byte_array: bytearray, fh: FileHandle) -> int:
    retval = None
    try:
        if byte_array[199] != 0:
            retval = FILE_TABLE_FULL_ERROR
            raise MemoryError(colors.ERROR_RED + "File table full" + colors.END) 
        index = 101
        # If there is space in file table
        if retval == None:
            while True:
                if index == 131:
                    retval = DISC_FULL_ERROR
                    write_disc(bytes(byte_array))
                    raise MemoryError(colors.ERROR_RED + "Disc full unable to write to cluster 31 for file %s" % fh.name + colors.END) 
                if byte_array[index] == 0:
                    byte_array[index] = 255
                    byte_array[fh.active_cluster] = index
                    fh.active_cluster = index
                    retval = index
                    break
                index += 1
            print_color_wrapper("Extending file %s to the file table index: " % fh.name + str(index), colors.INFO_CYAN)
            write_disc(bytes(byte_array))
        return retval
    except Exception:
        traceback.print_exc()
        return retval

""" Writes new file data to the root cluster. """
def root_cluster_write_new_file(filename: str, byte_array: bytearray, root_index: int, file_cluster: int) -> FileHandle:
    try:
        print_color_wrapper("Writing new file %s to the root cluster index: " % filename + str(root_index), colors.OK_GREEN)
        fh = FileHandle()

        # Set file handle origin position
        fh.origin = root_index

        # Set file name
        byte_array[root_index] = ord(filename)
        fh.name = filename

        # Set last file position
        root_index += 1
        byte_array[root_index] = file_cluster
        fh.position = byte_array[root_index]

        # Set file cluster size
        root_index += 1
        byte_array[root_index] = 1
        fh.size = 1

        write_disc(bytes(byte_array))
        return fh
    except Exception:
        traceback.print_exc()
        return None

""" Returns file handle for a new file. """
def set_file_handle(byte_array: bytearray, filename: str) -> FileHandle:
    retval = None
    try:
        root_index = find_root_cluster(byte_array, ROOT_CLUSTER_START)
        root_index = (root_index % 100) * 100
        print_color_wrapper("Searching for free root cluster space from index: " + str(root_index), colors.INFO_YELLOW + colors.UNDERLINE)
        root_cluster_end = root_index + 99
        if check_root_cluster_write_space(byte_array, root_cluster_end):
            while(True):
                # if root cluster index is empty start writing
                if byte_array[root_index] == 0:
                    retval = file_table_write_new_file(byte_array, filename)
                    if retval == FILE_TABLE_FULL_ERROR: 
                        raise MemoryError(colors.ERROR_RED + "File table full, unable to open file %s" % filename + colors.END) 
                    elif retval == DISC_FULL_ERROR: 
                        raise MemoryError(colors.ERROR_RED + "Disc full, unable to open file %s" % filename + colors.END)
                    elif retval != None:
                        file_table_cluster = retval
                    retval = root_cluster_write_new_file(filename, byte_array, root_index, file_table_cluster)
                    break
                else:
                    root_index += 1
        else:
            retval = DISC_FULL_ERROR
            raise MemoryError(colors.ERROR_RED + "Disc full, unable to open root cluster for file %s" % filename + colors.END) 
        return retval
    except Exception:
        traceback.print_exc()
        return retval

""" Find active root cluster. """
def find_root_cluster(byte_array: bytearray, index: int) -> int:
    if byte_array[index] == 255:
        return index
    else:
        index = find_root_cluster(byte_array, index)
        return index

""" Check if root cluster has enough data for new file write. """
def check_root_cluster_write_space(byte_array: bytearray, index: int) -> bool:
    if byte_array[index] == 0 and byte_array[index-1] == 0 and byte_array[index-2] == 0:
        return True
    else:
        return False

""" Prints cluster content. """
def print_clusters(num: int = 27) -> None:
    disc = read_disc()
    int_array = [int(byte) for byte in disc] 
    start_index = 100
    print_color_wrapper("\n#####################################", colors.INFO_YELLOW)
    print_color_wrapper("########## FIRST CLUSTER ############", colors.INFO_YELLOW)
    print(disc[:start_index])
    print_color_wrapper("########## FILE TABLE CLUSTER #######", colors.INFO_YELLOW)
    print(int_array[start_index:start_index+30])
    start_index += 100
    print_color_wrapper("########## ROOT CLUSTER #############", colors.INFO_YELLOW)
    print(int_array[start_index:start_index+100])
    start_index += 100

    for i in range(num):
        print_color_wrapper("########## FILE CLUSTER %s ###########"%(i+4), colors.INFO_DARK_CYAN)
        print(disc[start_index:start_index + 100])
        start_index += 100
    print_color_wrapper("\n#####################################", colors.INFO_DARK_CYAN)
    print()

""" Write data to file. """
def write_file(fh: FileHandle, buffer: str) -> None:
    try:
        first_cluster_index = 0
        first_cluster_flag = False
        disc = read_disc()
        byte_array = bytearray(disc)
        fh.active_cluster = fh.position
        cluster_index = (fh.position % 100) * 100
        while True:
            if byte_array[cluster_index] == 0:
                # set first cluster index to enable data append
                if first_cluster_flag == False:
                    first_cluster_flag = True
                    first_cluster_index = cluster_index
                    first_cluster_index = round(first_cluster_index / 100) * 100
                cnt = 0
                for i in buffer:
                    index = cluster_index + cnt
                    if index > first_cluster_index + CLUSTER_SIZE:
                        retval = file_table_extend_file(byte_array, fh)
                        if retval != DISC_FULL_ERROR and retval != FILE_TABLE_FULL_ERROR:
                            # calculate starting index
                            cluster_index = (retval % 100) * 100
                            # set starting index for the new cluster
                            first_cluster_index = cluster_index
                            # counter reset
                            cnt = 0
                            index = cluster_index + cnt

                            # increment file size
                            fh.size = fh.size + 1
                            byte_array[fh.origin + 2] = fh.size
                        else:
                            # reset to starting position
                            return retval
                    if index > MAX_DISC_SIZE:
                        write_disc(bytes(byte_array))
                        raise MemoryError(colors.ERROR_RED + "Disc full, unable to write beyond index 3000 for file %s" % fh.name + colors.END)
                    byte_array[index] = ord(i)
                    cnt += 1
                print_color_wrapper("Buffer data: %s successfully written to file %s" % (buffer[:10], fh.name), colors.INFO_ORANGE)
                write_disc(bytes(byte_array))
                break
            cluster_index += 1
    except Exception:
        traceback.print_exc()

""" Close file. """
def close_file(fh: FileHandle) -> bool:
    try:
        print_color_wrapper("File %s closed"%fh.name, colors.INFO_CYAN)
        del fh
        return True
    except Exception:
        traceback.print_exc()
        return False

""" Deletes file. """
def delete_file(fh: FileHandle, filename: str) -> None:
    if fh != DISC_FULL_ERROR and FILE_TABLE_FULL_ERROR:
        disc = read_disc()
        byte_array = bytearray(disc)
        file_position = fh.position

        # Deleting data from the root cluster
        byte_array[fh.origin] = 0
        byte_array[fh.origin+1] = 0
        byte_array[fh.origin+2] = 0

        # Deleting data from file clusters
        for i in range (fh.size):
            # Deleting data from the file table cluster
            byte_array[file_position] = 0
            cluster_index = (file_position % 100) * 100
            for i in range(100):
                byte_array[cluster_index + i] = 0
            file_position += 1
        write_disc(bytes(byte_array))
    else:
        print_color_wrapper("Unable to delete file %s, file handle invalid" % filename, colors.ERROR_RED)

""" Wrapper function for opening and writing to a file. """
def open_write_file(data: str, len: int) -> FileHandle:
    fh = open_file(data)
    if fh != DISC_FULL_ERROR and FILE_TABLE_FULL_ERROR:
        write_file(fh, fh.name * len)
    return fh

""" Deletes disc file. """
def delete_disc() -> None:
    os.remove("disc")
    print_color_wrapper("Disc simulation file deleted", colors.BOLD + colors.INFO_PURPLE)

""" Appends data to already opened file. """
def append_file(fh: FileHandle, data: str, len: int) -> None:
    if fh != DISC_FULL_ERROR and FILE_TABLE_FULL_ERROR:
        write_file(fh, data * len)

############## APPLICATION START ##############

if __name__ == "__main__":

    # Read or create new disc
    disc = mount_disc()

    # Write data
    fh_1 = open_write_file("a", 110) 
    fh_2 = open_write_file("b", 510)
    open_write_file("c", 310)
    fh_4 = open_write_file("d", 310)
    open_write_file("e", 310)
    open_write_file("f", 410)

    # Append data
    append_file(fh_1, "z", 50)

    # Delete data
    delete_file(fh_2, "b")
    delete_file(fh_4, "d")

    # Deplete remaining empty disc space
    open_write_file("g", 10000)

    # Print all cluster data
    print_clusters()

    # Saves current disc data and remove reference for disc object
    unmount_disc()

    # Delete disc file
    delete_disc()