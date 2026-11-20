import unittest
from app.operations import calculate


class OperationsTest(unittest.TestCase):
    def test_results(self):
        for op, expected in [('add',15),('multiply',36),('divide',4)]:
            with self.subTest(op=op):
                self.assertEqual(calculate({'id':'test','operation':op,'args':[12,3]}),expected)

    def test_zero_division(self):
        with self.assertRaises(ZeroDivisionError):
            calculate({'id':'test','operation':'divide','args':[1,0]})

    def test_invalid_payloads(self):
        for job in [None, [], {}, {'id':'test'},
                    {'id':'test','operation':'unknown','args':[1,2]},
                    {'id':'test','operation':'add','args':[True,2]},
                    {'id':'test','operation':'add','args':[float('nan'),2]}]:
            with self.subTest(job=job), self.assertRaises(ValueError): calculate(job)
