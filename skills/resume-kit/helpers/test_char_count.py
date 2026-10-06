#!/usr/bin/env python3
import sys
import unittest
from char_count import strip_latex, count_bold_chars, classify_bullet

class TestCharCount(unittest.TestCase):
    def test_strip_latex_basic(self):
        text = r"\textbf{DFT} analysis of \ce{TiO2} surfaces"
        expected = "DFT analysis of TiO2 surfaces"
        self.assertEqual(strip_latex(text), expected)

    def test_strip_latex_greek(self):
        text = r"Designed a new method using $\beta$-alanine"
        expected = "Designed a new method using G-alanine"
        self.assertEqual(strip_latex(text), expected)

    def test_bold_count(self):
        text = r"\textbf{DFT} and \textbf{molecular dynamics}"
        self.assertEqual(count_bold_chars(text), len("DFT") + len("molecular dynamics"))

    def test_classification_resume(self):
        # 1L resume bullet
        variant, status, lo, hi, hard_max, orphan, eff = classify_bullet(108, 0, 'resume')
        self.assertEqual(variant, '1L')
        self.assertEqual(status, 'OK')

        # 2L resume bullet
        variant, status, lo, hi, hard_max, orphan, eff = classify_bullet(200, 0, 'resume')
        self.assertEqual(variant, '2L')
        self.assertEqual(status, 'OK')

if __name__ == '__main__':
    unittest.main()
