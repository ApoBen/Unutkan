# -*- coding: utf-8 -*-
"""
Unutkan Core Module - Birim Testleri
"""

import os
import tempfile
import unittest
import zipfile
import core

class TestUnutkanCore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    # --- 1. Path Validation Tests ---
    def test_validate_file_path_valid(self):
        file_path = os.path.join(self.temp_dir.name, "test.txt")
        with open(file_path, "w") as f:
            f.write("hello")
        valid, real_path, err = core.validate_file_path(file_path)
        self.assertTrue(valid)
        self.assertEqual(real_path, os.path.realpath(file_path))
        self.assertEqual(err, "")

    def test_validate_file_path_nonexistent(self):
        file_path = os.path.join(self.temp_dir.name, "doesnotexist.txt")
        valid, real_path, err = core.validate_file_path(file_path)
        self.assertFalse(valid)

    def test_validate_file_path_symlink(self):
        real_file = os.path.join(self.temp_dir.name, "real.txt")
        link_file = os.path.join(self.temp_dir.name, "link.txt")
        with open(real_file, "w") as f:
            f.write("data")
        os.symlink(real_file, link_file)

        valid, real_path, err = core.validate_file_path(link_file)
        self.assertFalse(valid)
        self.assertIn("Sembolik linkler", err)

    # --- 2. Text Sanitizer Tests ---
    def test_sanitize_text_urls(self):
        raw = "Check this link: https://example.com/item?utm_source=twitter&fbclid=12345&id=99"
        sanitized = core.sanitize_text(raw, {'urls': True, 'emails': False, 'phones': False, 'secrets': False})
        self.assertNotIn("utm_source", sanitized)
        self.assertNotIn("fbclid", sanitized)
        self.assertIn("id=99", sanitized)

    def test_sanitize_text_email(self):
        raw = "Contact me at user.name@domain.com or info@test.org"
        sanitized = core.sanitize_text(raw, {'urls': False, 'emails': True, 'phones': False, 'secrets': False})
        self.assertNotIn("user.name@domain.com", sanitized)
        self.assertIn("@domain.com", sanitized)

    def test_sanitize_text_phone(self):
        raw = "My number is 0532 123 45 67 or +90 555 987 65 43"
        sanitized = core.sanitize_text(raw, {'urls': False, 'emails': False, 'phones': True, 'secrets': False})
        self.assertNotIn("0532 123 45 67", sanitized)
        self.assertNotIn("+90 555 987 65 43", sanitized)

    def test_sanitize_text_secrets(self):
        raw = "My key is AIzaSy1234567890123456789012345678901 and AWS is AKIAIOSFODNN7EXAMPLE"
        sanitized = core.sanitize_text(raw, {'urls': False, 'emails': False, 'phones': False, 'secrets': True})
        self.assertNotIn("AIzaSy1234567890123456789012345678901", sanitized)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", sanitized)
        self.assertIn("[GOOGLE_API_KEY_SECRET]", sanitized)
        self.assertIn("[AWS_API_KEY_SECRET]", sanitized)

    # --- 3. Shredder Tests ---
    def test_shred_file(self):
        file_path = os.path.join(self.temp_dir.name, "to_shred.txt")
        with open(file_path, "wb") as f:
            f.write(b"Sensitive secret data " * 100)

        self.assertTrue(os.path.exists(file_path))
        success, err = core.shred_file(file_path, method_index=0)
        self.assertTrue(success)
        self.assertFalse(os.path.exists(file_path))

    # --- 4. Office Metadata Cleaner Tests ---
    def test_clean_office_metadata(self):
        docx_path = os.path.join(self.temp_dir.name, "sample.docx")
        with zipfile.ZipFile(docx_path, 'w') as z:
            z.writestr('docProps/core.xml', '<cp:coreProperties><dc:creator>John Doe</dc:creator></cp:coreProperties>')
            z.writestr('docProps/app.xml', '<Properties><Company>Secret Corp</Company></Properties>')
            z.writestr('word/document.xml', '<w:document><w:body><w:p/></w:body></w:document>')

        # Extract metadata test
        meta = core.extract_file_metadata(docx_path)
        self.assertIn("Office: creator", meta)
        self.assertEqual(meta["Office: creator"], "John Doe")

        # Clean file test
        success, out_path, err = core.clean_file(docx_path, overwrite=True)
        self.assertTrue(success)

        # Verify core.xml and app.xml are blanked out
        with zipfile.ZipFile(docx_path, 'r') as z:
            core_xml = z.read('docProps/core.xml').decode('utf-8')
            app_xml = z.read('docProps/app.xml').decode('utf-8')
            self.assertNotIn("John Doe", core_xml)
            self.assertNotIn("Secret Corp", app_xml)

    # --- 5. RamVault Tests ---
    def test_ram_vault_wipe(self):
        vault = core.RamVault()
        vault.mem_text = bytearray(b"Secret Vault Content")
        vault.mem_files["secret.dat"] = bytearray(b"Binary Data")

        self.assertIsNotNone(vault.mem_text)
        self.assertEqual(len(vault.mem_files), 1)

        vault.wipe()

        self.assertIsNone(vault.mem_text)
        self.assertEqual(len(vault.mem_files), 0)

if __name__ == '__main__':
    unittest.main()
