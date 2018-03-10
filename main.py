# The application of Kalman Filtering to the analysis
# of baseline 1D location data (BLE RSSIs)
# by Jesion

import plotly.plotly
from plotly.graph_objs import *
import datetime, math
import logging
import unittest

logging.basicConfig(
    filename="debug.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )

FILENAME = 'testData1.txt'
NODES_NB = 3

# Filter parameters
FILTER_R = 0.008
FILTER_Q = 0.1


class DataStream(object):
    """
    A few method to operate on raw data set.
    Purpose: convert data from "T=1:N=3:RSSI=-65;17:40:36;" to:
    {'node': 3, 'rssi': -51, 'tag': 1, 'dist': 4.396784253182812, 'ts': datetime.datetime(2018, 2, 20, 17, 40, 29)}
    """
    cov = float('nan')
    x = float('nan')

    def __init__(self, file_name):
        """
        Constructor with automatic data loader
        """
        self.file_name = file_name

        self.A = 1
        self.B = 0
        self.C = 1
        self.R = FILTER_R
        self.Q = FILTER_Q

        self.data_stream = self.load_data()

    def load_data(self):
        """
        Open a local disk file (raw data)
        :return: a list of raw records
        """
        logging.debug('Loading data from file ({})...'.format(self.file_name))
        with open(self.file_name, 'r') as data:
            readed_text = data.read()
        data_stream = readed_text.split(';\n')
        logging.debug('  {} records loaded.'.format(len(data_stream)))
        return self.parse_data(data_stream)

    def parse_data(self, data):
        """
        Parse raw data to structured dictionary
        :param data: raw list of records
        :return: parsed list of structured dictionary data
        """
        # TODO replace with regex
        parsed_data = []
        for item in data:
            if item:
                temp = {}
                temp['tag'] = int(item.split(':')[0][-1])
                temp['node'] = int(item.split(':')[1][-1])
                rssi = int(item.split(':')[2].split(';')[0][5:])
                temp['rssi'] = rssi
                temp['dist'] = self.calculate_distance(rssi)
                # temp['f_dist'] = self.kalman_filter(self.calculate_distance(rssi))
                temp['ts'] = datetime.datetime(2018, 02, 20, int(item.split(';')[1][:2]),
                                               int(item.split(';')[1][3:5]),
                                               int(item.split(';')[1][6:]))
                parsed_data.append(temp)

        # Applying filter to specific nodes
        for node in range(1, NODES_NB + 1):
            for item in parsed_data:
                if item['node'] == node:
                    item['f_dist'] = self.kalman_filter(item['dist'])

            # Reset Kalman variables
            self.x = float('nan')
            self.cov = float('nan')

        return parsed_data

    def get_data(self):
        """
        Get a whole dataset of structured data
        :return: list of structured dictionary data
        """
        return self.data_stream

    def kalman_filter(self, measurement):
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


class VisualizeData():
    """
    Plot data on the diagram (plot.ly)
    """
    def __init__(self, data):
        self.data = data
        logging.debug('VisualizedData - initialize')

    def plot_graph(self, dataset):
        """
        Plot diagram on the server (plotly)
        :param dataset: choose 'rssi', 'dist', or 'f_dist'
        """
        data = self.data
        nodes = []

        for node in range(1, NODES_NB + 1):
            data_x, data_y = [], []
            for item in data:
                if item['node'] == node:
                    data_x.append(item['ts'])
                    data_y.append(item[dataset])
            nodes.append(Scatter(x=data_x, y=data_y))

        data = Data(nodes)
        plotly.plotly.plot(data, filename=dataset+'-line')


class TestData(unittest.TestCase):

    def test_loader(self):
        data = DataStream(FILENAME)
        self.assertGreater(len(data.get_data()), 1)

    def test_parser(self):
        data = DataStream(FILENAME)
        self.assertEqual(data[0].keys(), ['node', 'dist', 'f_dist', 'ts', 'tag', 'rssi'])

    def test_filter(self):
        data = DataStream(FILENAME)
        test_data = [23, 65]
        filtered_data = []
        for i in test_data:
            filtered_data.append(data.kalman_filter(i))
        self.assertEqual(filtered_data[1], 44.80769230769231)


if __name__ == '__main__':
    # unittest.main()
    VisualizeData(DataStream(FILENAME)).plot_graph('f_dist')
    logging.debug('----------------Program ended OK!')
