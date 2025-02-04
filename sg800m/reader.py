import json

class Reader:
    def __init__(self):
        self.simSettings = json.load(open(f".\config\simSettings.json"))

        if self.simSettings == None:
            raise FileNotFoundError("SimSettings.json not found")

        if self.simSettings["switches"]["remote"] == True:
            self.getRemoteFilePaths()
        else:
            self.getLocalFilePaths()
        pass

    def getRemoteFilePaths(self):
        f = self.simSettings["file_explorer"]["remote_server"]
        if f == "idun":
            self.physStatesFilePaths = self.simSettings["file_explorer"]["remote"]["idun_dir_prefix"]
            self.trajectoryFilePaths = self.simSettings["file_explorer"]["remote"]["idun_dir_prefix"]
        else:
            self.physStatesFilePaths = self.simSettings["file_explorer"]["remote"]["saga_dir_prefix"]
            self.trajectoryFilePaths = self.simSettings["file_explorer"]["remote"]["saga_dir_prefix"]
        pass

    def getLocalFilePaths(self): 
        self.trajectoryFilePaths = self.simSettings["file_explorer"]["local"]["local_dir_prefix"]
        if self.simSettings["file_explorer"]["local"]["local_dir_prefix"] == "IDUN":
            self.trajectoryFilePaths = self.simSettings["file_explorer"]["local"]["idun_dir_prefix"]
        elif self.simSettings["file_explorer"]["local"]["local_dir_prefix"] == "SAGA":
            self.trajectoryFilePaths = self.simSettings["file_explorer"]["local"]["saga_dir_prefix"]
        self.physStatesFilePaths = self.simSettings["file_explorer"]["local"]["local_dir_prefix"]
        
        pass

