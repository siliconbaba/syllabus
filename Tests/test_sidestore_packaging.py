import importlib.util
from pathlib import Path
import plistlib
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('packager', Path(__file__).resolve().parents[1] / 'scripts/package_sidestore.py')
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)

class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = self.root / 'Original.app'
        self.app.mkdir()
        self.info = {'CFBundleIdentifier': 'com.example.book', 'CFBundleName': 'Original', 'CFBundleDisplayName': 'Русское название', 'CFBundleExecutable': 'Book', 'CFBundleSupportedPlatforms': ['iPhoneOS'], 'DTPlatformName': 'iphoneos'}
        (self.app / 'Info.plist').write_bytes(plistlib.dumps(self.info))
        (self.app / 'Book').write_bytes(b'fixture')
        (self.app / 'Book').chmod(0o755)

    def test_appledouble_removed_and_source_untouched(self):
        (self.app / '._Book').write_bytes(b'metadata')
        (self.app / '__MACOSX').mkdir()
        (self.app / '__MACOSX' / 'ignored').write_bytes(b'metadata')
        target = self.root / 'Copy.app'
        packager.clean_copy(self.app, target)
        self.assertFalse((target / '._Book').exists())
        self.assertFalse((target / '__MACOSX').exists())
        self.assertTrue((self.app / '._Book').exists())
        self.assertEqual((target / 'Book').stat().st_mode & 0o777, 0o755)

    def test_ascii_base_and_preserved_localization_keys(self):
        localized = self.app / 'ru.lproj' / 'InfoPlist.strings'
        localized.parent.mkdir()
        localized.write_bytes(plistlib.dumps({'OtherKey': 'Не потерять'}))
        packager.localize_name(self.app, 'InteractiveBook')
        result = plistlib.loads((self.app / 'Info.plist').read_bytes())
        self.assertEqual(result['CFBundleDisplayName'], 'InteractiveBook')
        self.assertEqual(result['CFBundleIdentifier'], self.info['CFBundleIdentifier'])
        self.assertEqual(plistlib.loads(localized.read_bytes()), {'OtherKey': 'Не потерять', 'CFBundleDisplayName': 'Русское название'})

    def test_existing_russian_display_name_preserved(self):
        localized = self.app / 'ru.lproj' / 'InfoPlist.strings'
        localized.parent.mkdir()
        localized.write_bytes(plistlib.dumps({'CFBundleDisplayName': 'Название для России'}))
        packager.localize_name(self.app, 'InteractiveBook')
        self.assertEqual(plistlib.loads(localized.read_bytes())['CFBundleDisplayName'], 'Название для России')

    def test_symlink_and_signing_resources_rejected(self):
        (self.app / 'linked').symlink_to('/tmp')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            packager.clean_copy(self.app, self.root / 'Copy.app')
        (self.app / 'linked').unlink()
        (self.app / 'embedded.mobileprovision').write_bytes(b'fixture')
        with self.assertRaisesRegex(ValueError, 'unsigned'):
            packager.clean_copy(self.app, self.root / 'Second.app')

    def test_does_not_overwrite_existing_release(self):
        output = self.root / 'existing.ipa'
        output.write_bytes(b'previous release')
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            packager.package(self.app, output)
        self.assertEqual(output.read_bytes(), b'previous release')

    def test_refuses_output_inside_source(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            packager.package(self.app, self.app / 'nested.ipa')

    def test_simulator_rejected_before_binary_inspection(self):
        self.info['CFBundleSupportedPlatforms'] = ['iPhoneSimulator']
        (self.app / 'Info.plist').write_bytes(plistlib.dumps(self.info))
        with self.assertRaisesRegex(ValueError, 'iPhoneOS'):
            packager.inspect_bundle(self.app)

if __name__ == '__main__':
    unittest.main()
