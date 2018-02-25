# Data analytics with Kalman filtering
# by Jesion

import plotly.plotly as py
from plotly.graph_objs import *
import datetime, math


class DataStream(object):
    """
    A few method to operate on raw data set.
    Purpose: convert data from "T=1:N=3:RSSI=-65;17:40:36;" to:
    {'node': 3, 'rssi': -51, 'tag': 1, 'dist': 4.396784253182812, 'ts': datetime.datetime(2018, 2, 20, 17, 40, 29)}
    """
    def __init__(self):
        """
        Constructor with automatic data loader
        """
        self.dataStream = self.parseData(self.loadData())

    def loadData(self):
        """
        Load file from the disk
        :return: a list of raw records
        """
        FILENAME = 'testData1.txt'
        print("Loading data from file...")
        inFile = open(FILENAME, 'r')
        readed_text = inFile.read()
        dataStream = readed_text.split(';\n')
        print "  ", len(dataStream), "records loaded."
        return dataStream

    def parseData(self, data):
        """
        Parse raw data to structured dictionary
        :param data: raw list of records
        :return: parsed list of structured dictionary data
        """
        parsed_data = []
        dist = CalculateDistance()
        for item in data:
            if item:
                temp = {}
                temp['tag'] = int(item.split(':')[0][-1])
                temp['node'] = int(item.split(':')[1][-1])
                rssi = int(item.split(':')[2].split(';')[0][5:])
                temp['rssi'] = rssi
                temp['dist'] = dist.calculateDistance(rssi)
                temp['ts'] = datetime.datetime(2018, 02, 20, int(item.split(';')[1][:2]),
                                               int(item.split(';')[1][3:5]),
                                               int(item.split(';')[1][6:]))
                parsed_data.append(temp)
        return parsed_data

    def getAllData(self):
        """
        Get a whole dataset of structured data
        :return: list of structured dictionary data
        """
        return self.dataStream


class CalculateDistance:

    def calculateDistance(self, rssi):
        """
        Convert RSSI to real world meters
        :param rssi:
        :return: The distance converted from RSSI (in meters)
        """
        txPower = -50
        if rssi == 0:
            return -1
        ratio = abs(rssi * 1.0 / txPower)
        if ratio < 1.0:
            return ratio ** 10
        else:
            distance = (3) * (ratio ** 4.595) + 1.111
            return distance


class KalmanFilter:

    cov = float('nan')
    x = float('nan')

    def __init__(self, R, Q):
        """
        Constructor
        :param R: Process Noise
        :param Q: Measurement Noise
        """
        self.A = 1
        self.B = 0
        self.C = 1

        self.R = R
        self.Q = Q

    def filter(self, measurement):
        """
        Filters a measurement
        :param measurement: The measurement value to be filtered
        :return: The filtered value
        """
        u = 0
        if math.isnan(self.x):
            self.x = (1 / self.C) * measurement
            self.cov = (1 / self.C) * self.Q * (1 / self.C)
        else:
            predX = (self.A * self.x) + (self.B * u)
            predCov = ((self.A * self.cov) * self.A) + self.R

            # Kalman Gain
            K = predCov * self.C * (1 / ((self.C * predCov * self.C) + self.Q));

            # Correction
            self.x = predX + K * (measurement - (self.C * predX));
            self.cov = predCov - (K * self.C * predCov);

        return self.x


class VisualizeData:
    """
    Plot data on the diagram (plot.ly)
    """
    def __init__(self, data):
        self.data = data

    def plotGraphAllRSSI(self):
        """
        Showing raw RSSI data
        """
        data = self.data
        data_x, data_y = [], []
        for item in data:
            if item['node'] == 1:
                data_x.append(item['ts'])
                data_y.append(item['rssi'])
        node1 = Scatter(x=data_x, y=data_y)

        data_x, data_y = [], []
        for item in data:
            if item['node'] == 2:
                data_x.append(item['ts'])
                data_y.append(item['rssi'])
        node2 = Scatter(x=data_x, y=data_y)

        data_x, data_y = [], []
        for item in data:
            if item['node'] == 3:
                data_x.append(item['ts'])
                data_y.append(item['rssi'])
        node3 = Scatter(x=data_x, y=data_y)

        data = Data([node1, node2, node3])

        py.plot(data, filename='rssi-line')
        return True

    def plotGraphDistance(self, filtered=1):
        """
        Showing data converted to real world distances
        :param filtered: 1 Kalman filtered, 2 non-filtered
        :return: True if everything was OK, False otherwise
        """
        data = self.data
        data_x, data_y = [], []
        for item in data:
            if item['node'] == 2:
                data_x.append(item['ts'])
                data_y.append(item['dist'])
        node1 = Scatter(x=data_x, y=self.filterKalman(data_y))

        data_x, data_y = [], []
        for item in data:
            if item['node'] == 3:
                data_x.append(item['ts'])
                data_y.append(item['dist'])
        node2 = Scatter(x=data_x, y=self.filterKalman(data_y))

        data = Data([node1, node2])

        py.plot(data, filename='distance-line')
        return True


    def filterKalman(self, data, a=0.008, b=0.1):
        """
        Kalman filtering on a set of data
        :param data: list of raw data
        :param a: Process Noise
        :param b: Measurement Noise
        :return: [LIST] filtered data
        """
        kalman = KalmanFilter(a, b)
        data_filtered = []
        for i in data:
            data_filtered.append(kalman.filter(i))
        return data_filtered


app = DataStream()
visualize = VisualizeData(app.getAllData()).plotGraphDistance()
