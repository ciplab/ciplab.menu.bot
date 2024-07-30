import unittest


from menu_random_sample import lambda_handler


class TestMenuRandomSample(unittest.TestCase):
    def test_lambda_handler(self):
        event = {}
        context = {}
        lambda_handler(event, context)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
