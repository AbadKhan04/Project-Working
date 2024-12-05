import unittest
import os

class TestYOLOFilePaths(unittest.TestCase):
    def setUp(self):
        # Define the file paths to test
        self.yolo_config = 'Datasets/yolov3-tiny.cfg'
        self.yolo_weights = 'Datasets/yolov3-tiny.weights'
        self.coco_names = 'Datasets/coco.names'

    def test_yolo_config_exists(self):
        """Test if YOLO config file exists."""
        self.assertTrue(os.path.exists(self.yolo_config), f"Config file not found: {self.yolo_config}")

    def test_yolo_weights_exists(self):
        """Test if YOLO weights file exists."""
        self.assertTrue(os.path.exists(self.yolo_weights), f"Weights file not found: {self.yolo_weights}")

    def test_coco_names_exists(self):
        """Test if COCO names file exists."""
        self.assertTrue(os.path.exists(self.coco_names), f"Names file not found: {self.coco_names}")

if __name__ == '__main__':
    unittest.main()
