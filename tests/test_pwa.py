import json
from pathlib import Path
import struct
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]

class PwaTests(TestCase):
    def test_manifest_icons_exist_with_correct_dimensions(self):
        manifest = json.loads((ROOT/'static/pwa/manifest.json').read_text())
        self.assertEqual(manifest['name'], 'Daniel Mbuvi Mulatya')
        self.assertEqual(manifest['scope'], '/')
        self.assertEqual({icon['purpose'] for icon in manifest['icons']}, {'any', 'maskable'})
        for icon in manifest['icons']:
            data=(ROOT/icon['src'].lstrip('/')).read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            width,height=struct.unpack('>II',data[16:24])
            self.assertEqual(f'{width}x{height}', icon['sizes'])
        self.assertFalse((ROOT/'static/img/cm.png').exists())

    def test_root_worker_route_and_public_head(self):
        from app import app
        client=app.test_client()
        with client.get('/service-worker.js') as response:
            self.assertEqual(response.status_code,200)
            self.assertIn('javascript',response.content_type)
            self.assertEqual(response.headers['Service-Worker-Allowed'],'/')
            self.assertEqual(response.headers['Cache-Control'],'no-cache')
        body=client.get('/dashboard/login').get_data(as_text=True)
        self.assertIn('/static/pwa/manifest.json',body)
        self.assertIn('/static/pwa/apple-touch-icon.png',body)
        self.assertNotIn('cm.png',body)
        self.assertEqual(body.count('rel="manifest"'),1)
        self.assertNotIn("register('/static/pwa/sw.js')",body)
