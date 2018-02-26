# The application of Kalman Filtering to the analysis
# of baseline 1D location data (BLE RSSIs)
# by Jesion

import plotly.plotly as py
from plotly.graph_objs import *
import datetime, math

FILENAME = 'testData1.txt'


class DataStream:
    """
    A few method to operate on raw data set.
    Purpose: convert data from "T=1:N=3:RSSI=-65;17:40:36;" to:
    {'node': 3, 'rssi': -51, 'tag': 1, 'dist': 4.396784253182812, 'ts': datetime.datetime(2018, 2, 20, 17, 40, 29)}
    """
    def __init__(self, file_name):
        """
        Constructor with automatic data loader
        """
        self.file_name = file_name
        self.data_stream = self.load_data()

    def load_data(self):
        """
        Open a local disk file (raw data)
        :return: a list of raw records
        """
        print 'Loading data from file ({})...'.format(self.file_name)
        with open(self.file_name, 'r') as data:
            readed_text = data.read()
        data.close()
        data_stream = readed_text.split(';\n')
        print '  {} records loaded.'.format(len(data_stream))
        return self.parse_data(data_stream)

    def parse_data(self, data):
        """
        Parse raw data to structured dictionary
        :param data: raw list of records
        :return: parsed list of structured dictionary data
        """
        parsed_data = []
        for item in data:
            if item:
                temp = {}
                temp['tag'] = int(item.split(':')[0][-1])
                temp['node'] = int(item.split(':')[1][-1])
                rssi = int(item.split(':')[2].split(';')[0][5:])
                temp['rssi'] = rssi
                temp['dist'] = self.calculate_distance(rssi)
                temp['ts'] = datetime.datetime(2018, 02, 20, int(item.split(';')[1][:2]),
                                               int(item.split(';')[1][3:5]),
                                               int(item.split(';')[1][6:]))
                parsed_data.append(temp)
        return parsed_data

    def get_data(self):
        """
        Get a whole dataset of structured data
        :return: list of structured dictionary data
        """
        return self.data_stream

    def calculate_distance(self, rssi):
        """
        Convert RSSI to real world units (meters)
        :param rssi:
        :return: The distance converted from RSSI (in meters)
        """
        TX_POWER = -50

        if rssi == 0:
            return -1
        ratio = abs(rssi * 1.0 / TX_POWER)
        if ratio < 1.0:
            return ratio ** 10
        else:
            distance = (3) * (ratio ** 4.595) + 1.111
            return distance

    def __getitem__(self, item):
        return self.get_data()[item]


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
            pred_x = (self.A * self.x) + (self.B * u)
            pred_cov = ((self.A * self.cov) * self.A) + self.R

            # Kalman Gain
            k = pred_cov * self.C * (1 / ((self.C * pred_cov * self.C) + self.Q))

            # Correction
            self.x = pred_x + k * (measurement - (self.C * pred_x))
            self.cov = pred_cov - (k * self.C * pred_cov)

        return self.x


class VisualizeData:
    """
    Plot data on the diagram (plot.ly)
    """
    def __init__(self, data):
        self.data = data

    def plot_graph_all_rssi(self):
        """
        Tracing raw RSSI data
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

    def plot_graph_distance(self, filtered=1):
        """
        Trasing data converted to real world distances
        :param filtered: 1 Kalman filtered, 2 non-filtered
        :return: True if everything was OK, False otherwise
        """
        data = self.data
        data_x, data_y = [], []
        for item in data:
            if item['node'] == 2:
                data_x.append(item['ts'])
                data_y.append(item['dist'])
        node1 = Scatter(x=data_x, y=self.filter_kalman(data_y))

        data_x, data_y = [], []
        for item in data:
            if item['node'] == 3:
                data_x.append(item['ts'])
                data_y.append(item['dist'])
        node2 = Scatter(x=data_x, y=self.filter_kalman(data_y))

        data = Data([node1, node2])

        py.plot(data, filename='distance-line')

    def filter_kalman(self, data, a=0.008, b=0.1):
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


VisualizeData(DataStream(FILENAME)).plot_graph_distance()
