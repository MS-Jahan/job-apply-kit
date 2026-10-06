import importlib, os, unittest
from unittest import mock

import _paths  # noqa: F401


class CdpTests(unittest.TestCase):
    def test_port_from_env(self):
        try:
            import websocket  # noqa: F401
        except ImportError:
            self.skipTest("websocket-client not installed")
        with mock.patch.dict(os.environ, {"JAK_CDP_PORT": "9333"}):
            import cdp
            importlib.reload(cdp)
            self.assertEqual(cdp.PORT, 9333)
            self.assertEqual(cdp.DEV, "http://127.0.0.1:9333")
        importlib.reload(cdp)

    def test_picker_walk_prefers_pdf_accept(self):
        try:
            import websocket  # noqa: F401
        except ImportError:
            self.skipTest("websocket-client not installed")
        import picker_upload
        tree = {"nodeType": 1, "nodeName": "DIV", "children": [
            {"nodeType": 1, "nodeName": "INPUT", "nodeId": 1, "attributes": ["type", "file", "accept", "image/*"]},
            {"nodeType": 1, "nodeName": "IFRAME", "contentDocument": {"nodeType": 9, "children": [
                {"nodeType": 1, "nodeName": "INPUT", "nodeId": 2, "attributes": ["type", "file", "accept", ".pdf,application/pdf"]}]}},
        ]}
        found = []
        picker_upload.walk(tree, found)
        self.assertEqual([n for n, _ in found], [1, 2])


if __name__ == "__main__":
    unittest.main()
