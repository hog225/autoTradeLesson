import os

def findFileOndir(f_name):
    for file_name in os.listdir(os.getcwd()):
        if file_name == f_name:
            return True
    return False

if __name__ == "__main__":
    pass