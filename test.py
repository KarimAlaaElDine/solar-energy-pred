import unittest
import app.model.api_data as api_data
import pandas as pd

class TestAppData(unittest.TestCase):

    def test_get_weather_data(self):
        result = api_data.get_weather_data(40)
        self.assertEqual(result.shape, (41,4))
    
    def test_get_DK2_energy(self):
        result = api_data.get_DK2_energy(40)
        self.assertEqual(result.shape, (40,13))

    def test_get_features(self):
        result = api_data.get_features()
        self.assertEqual(result.shape , (1,40, 17))

if __name__ == '__main__':
    unittest.main()