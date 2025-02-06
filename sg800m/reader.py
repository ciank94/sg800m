import json
import datetime
import logging
import xarray
from xarray import date2num, num2date
import numpy as np

class Reader:
    def __init__(self, inputPath, outputPath, releaseNumber):
        self.inputPath = inputPath
        self.outputPath = outputPath
        self.releaseNumber = releaseNumber
        self.samplesPrefix = "samplesNSEW_"
        self.trajectoryFolder = inputPath + "trajectory/"
        self.simSettings = json.load(open(f".\config\simSettings.json"))
        if self.simSettings == None:
            raise FileNotFoundError("SimSettings.json not found")
        self.initLogger()
        self.timeSettings()
        self.getPhysFileName()
        self.getBioFileName()
        self.readPhysFile()
        self.readBioFile()
        self.physTimeIndex = None
        self.bioTimeIndex = None
        self.lastUpdateDay = None
        self.lastUpdateHour = None
        self.lastBioUpdateDay = None
        return

    def initLogger(self):
        # Clear existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        # Configure logging format
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_format)
        
        # File handler (overwrite mode)
        file_handler = logging.FileHandler(self.outputPath + "/reader.log", mode='w')
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"================={self.__class__.__name__}=====================")
        self.logger.info(f"Initializing {self.__class__.__name__}")
        self.logger.info(f"Input path: {self.inputPath}")
        self.logger.info(f"Output path: {self.outputPath}")
        self.logger.info(f"Release number: {self.releaseNumber}")
        self.logger.info(f"Duration days: {self.simSettings['duration_days']}")
        self.logger.info(f"Time step: {self.simSettings['time_step_minutes']} min")
        self.logger.info(f"Save step: {self.simSettings['save_step_hours']} h")
        self.logger.info(f"Number of particles: {self.simSettings['n']}")
        self.logger.info(f"Number of ensembles: {self.simSettings['N']}")
        self.logger.info(f"xmin - xmax: {self.simSettings['x_min']} - {self.simSettings['x_max']}")
        self.logger.info(f"ymin - ymax: {self.simSettings['y_min']} - {self.simSettings['y_max']}")
        return
    
    def timeSettings(self):
        year = self.simSettings["year"]
        month = self.simSettings["month"]
        day = self.simSettings["day"]
        dayIncrement = datetime.timedelta(days=self.releaseNumber)
        self.initDateTime = datetime.datetime(year, month, day, 1, 0, 0) + dayIncrement
        durationDays = datetime.timedelta(days=self.simSettings["duration_days"])
        self.duration = durationDays.days
        self.currentDateTime = self.initDateTime
        self.fileMonth = self.initDateTime.month
        self.fileYear = self.initDateTime.year
        self.logger.info(f"Datetime init: {self.initDateTime}")
        return 

    def getPhysFileName(self):
        self.samplesFolder = self.inputPath + "sg_phys_states/"
        self.physFileName = self.samplesFolder + self.samplesPrefix + str(self.fileYear) + \
                        str(self.fileMonth).zfill(2) + ".nc"
        self.logger.info(f"File name: {self.physFileName}")
        return

    def getBioFileName(self):
        self.bioFileName = self.samplesFolder + "CMEMS_SGBIO_Dfull_" + str(self.fileYear) + \
                        ".nc"
        self.logger.info(f"File name: {self.bioFileName}")
        return
    

    def readPhysFile(self):
        self.dsPhys = xarray.open_dataset(self.physFileName)
        self.logger.info(f"Dataset: {self.dsPhys}")
        return
    
    def readBioFile(self):
        self.dsBio = xarray.open_dataset(self.bioFileName)
        self.logger.info(f"Dataset: {self.dsBio}")
        return


    def update_time(self):
        """Update time and handle file transitions for physics and bio data"""
        # Calculate time step in timedelta
        time_step = datetime.timedelta(minutes=self.simSettings['time_step_minutes'])
        self.currentDateTime += time_step

        # Check if we need to load a new physics file (month changed)
        if self.currentDateTime.month != self.fileMonth:
            self.logger.info(f"Month changed from {self.fileMonth} to {self.currentDateTime.month}, loading new physics file")
            self.fileMonth = self.currentDateTime.month
            self.dsPhys.close()
            self.getPhysFileName()
            self.readPhysFile()

        # Find nearest time index in physics dataset
        phys_times = self.dsPhys.time.values
        current_np_datetime = np.datetime64(self.currentDateTime)
        
        if self.simSettings.get('test', False):  # Daily updates in test mode
            if self.currentDateTime.day != self.lastUpdateDay:
                self.physTimeIndex = np.argmin(np.abs(phys_times - current_np_datetime))
                self.lastUpdateDay = self.currentDateTime.day
                self.logger.debug(f"Updated physics time index to {self.physTimeIndex} (daily)")
        else:  # Hourly updates in normal mode
            if self.currentDateTime.hour != self.lastUpdateHour:
                self.physTimeIndex = np.argmin(np.abs(phys_times - current_np_datetime))
                self.lastUpdateHour = self.currentDateTime.hour
                self.logger.debug(f"Updated physics time index to {self.physTimeIndex} (hourly)")

        # Update bio time index (always daily)
        bio_times = self.dsBio.time.values
        if self.currentDateTime.day != self.lastBioUpdateDay:
            self.bioTimeIndex = np.argmin(np.abs(bio_times - current_np_datetime))
            self.lastBioUpdateDay = self.currentDateTime.day
            self.logger.debug(f"Updated bio time index to {self.bioTimeIndex}")

        return


def geo2grid(lat, lon, case):
    case_types = ["get_xy", "get_bl"]
    if case not in case_types:
        raise ValueError(
            "Invalid case type in 3rd argument. Expected one of: %s" % case_types
        )

    a = 6378206.4  # Earth Radius
    fm = 294.97870  # Inverse flattening
    f = 1 / fm  # Flattening
    e = math.sqrt((2 * f) - (f**2))  # Eccentricity
    lon_0 = -45.0  # False origin longitude
    lat_0 = -44.0  # False origin latitude
    lat_1 = -40  # First parallel
    lat_2 = -68  # Second parallel
    x_0 = -175200.0 / 800  # Easting at false origin
    y_0 = 1484800.0 / 800  # Northing at false origin
    dx = 0.8
    imax = 825  # Weddell Sea domain

    rval = len(lat)
    xs = np.empty(rval)
    ys = np.empty(rval)
    for i in range(rval):
        FiF = lat_0 * math.pi / 180
        Fi1 = lat_1 * math.pi / 180
        Fi2 = lat_2 * math.pi / 180
        LamdaF = lon_0 * math.pi / 180

        if case == "get_xy":
            Fi = lat[i] * math.pi / 180
            Lamda = lon[i] * math.pi / 180

        EF = x_0 * dx * 1000
        NF = y_0 * dx * 1000

        if case == "get_bl":
            E = lat[i] * dx * 1000
            N = lon[i] * dx * 1000

        m1 = math.cos(Fi1) / math.sqrt(1 - e**2 * (math.sin(Fi1)) ** 2)
        m2 = math.cos(Fi2) / math.sqrt(1 - e**2 * (math.sin(Fi2)) ** 2)

        t1 = math.tan(math.pi / 4 - Fi1 / 2) / (
            ((1 - e * math.sin(Fi1)) / (1 + e * math.sin(Fi1))) ** (e / 2)
        )
        t2 = math.tan(math.pi / 4 - Fi2 / 2) / (
            ((1 - e * math.sin(Fi2)) / (1 + e * math.sin(Fi2))) ** (e / 2)
        )
        tF = math.tan(math.pi / 4 - FiF / 2) / (
            ((1 - e * math.sin(FiF)) / (1 + e * math.sin(FiF))) ** (e / 2)
        )

        if case == "get_xy":
            t = math.tan(math.pi / 4 - Fi / 2) / (
                ((1 - e * math.sin(Fi)) / (1 + e * math.sin(Fi))) ** (e / 2)
            )

        n = (math.log(m1) - math.log(m2)) / (math.log(t1) - math.log(t2))
        F = m1 / (n * t1**n)
        rF = a * F * tF**n

        if case == "get_xy":
            r = a * F * t**n

        if case == "get_bl":
            rm = np.sign(n) * np.sqrt((E - EF) ** 2 + (rF - (N - NF)) ** 2)
            tm = (rm / (a * F)) ** (1 / n)
            Tetam = np.arctan((E - EF) / (rF - (N - NF)))
            Fim = np.pi / 2 - 2 * np.arctan(Tetam)
            for j in range(1, 9):
                Fi = np.pi / 2 - 2 * np.arctan(
                    tm * ((1 - e * np.sin(Fim)) / (1 + e * np.sin(Fim))) ** (e / 2)
                )
                if np.abs(Fi - Fim) < 1e-7:
                    break
                else:
                    Fim = Fi
            Lamda = Tetam / n + LamdaF
            xs[i] = Fi * 180 / math.pi
            ys[i] = Lamda * 180 / math.pi

        if case == "get_xy":
            Teta = n * (Lamda - LamdaF)
            x = EF + r * math.sin(Teta)
            y = NF + rF - r * math.cos(Teta)
            xs[i] = x / (dx * 1000)
            ys[i] = y / (dx * 1000)

    return xs, ys

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r
