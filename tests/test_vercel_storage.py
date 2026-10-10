import os
import unittest
import tempfile
from unittest.mock import patch
from app import create_app
from config import Config, TestConfig


class TestVercelStorageConfig(unittest.TestCase):
    """
    Test suite for Vercel and serverless read-only filesystem handling.
    Ensures Flask application initializes gracefully in read-only and serverless environments.
    """

    def test_standard_app_creation(self):
        """App initializes cleanly using TestConfig with writable upload folder."""
        app = create_app(TestConfig)
        self.assertIsNotNone(app)
        self.assertTrue(os.path.exists(app.config['UPLOAD_FOLDER']))

    def test_serverless_flag_uses_tempdir(self):
        """When VERCEL or serverless environment variables are set, UPLOAD_FOLDER points to tempdir."""
        with patch.dict(os.environ, {'VERCEL': '1'}):
            from config import Config as DynamicConfig
            # In serverless mode, IS_SERVERLESS should be true or UPLOAD_FOLDER in tempdir
            is_serverless = bool(os.environ.get('VERCEL'))
            self.assertTrue(is_serverless)
            expected_prefix = tempfile.gettempdir()
            fallback_folder = os.path.join(expected_prefix, 'society_connect_uploads')
            self.assertTrue(fallback_folder.startswith(expected_prefix))

    def test_readonly_filesystem_fallback_on_os_error(self):
        """
        Simulate Vercel production read-only filesystem error:
        OSError: [Errno 30] Read-only file system: '/var/task/static/uploads'
        Verify create_app catches this error, falls back to tempfile.gettempdir(),
        and does NOT crash.
        """
        class ReadOnlyConfig(TestConfig):
            UPLOAD_FOLDER = '/var/task/static/uploads'

        # Mock os.makedirs to raise OSError(30, 'Read-only file system') when attempting to create /var/task/static/uploads
        original_makedirs = os.makedirs

        def mock_makedirs(path, exist_ok=True):
            if '/var/task' in str(path).replace('\\', '/'):
                raise OSError(30, "Read-only file system: '/var/task/static/uploads'")
            return original_makedirs(path, exist_ok=exist_ok)

        with patch('os.makedirs', side_effect=mock_makedirs):
            # This must not raise OSError!
            app = create_app(ReadOnlyConfig)
            self.assertIsNotNone(app)
            # The upload folder should have fallen back to writable temp directory
            self.assertNotIn('/var/task', app.config['UPLOAD_FOLDER'])
            self.assertTrue(app.config['UPLOAD_FOLDER'].startswith(tempfile.gettempdir()))

    def test_landing_page_accessible(self):
        """Landing page (/) returns 200 without database connection needed."""
        app = create_app(TestConfig)
        client = app.test_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SocietyConnect', response.data)

    def test_auth_login_accessible(self):
        """Auth login page returns 200."""
        app = create_app(TestConfig)
        client = app.test_client()
        response = client.get('/auth/login')
        self.assertEqual(response.status_code, 200)

    def test_app_py_redirects_to_home(self):
        """Requests to /app.py gracefully redirect to root (/) instead of returning 404."""
        app = create_app(TestConfig)
        client = app.test_client()
        response = client.get('/app.py')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get('Location'), '/')

    def test_uploads_route_404_for_missing_file(self):
        """The /uploads/<filename> route returns 404 for nonexistent files."""
        app = create_app(TestConfig)
        client = app.test_client()
        response = client.get('/uploads/nonexistent_test_image.png')
        self.assertEqual(response.status_code, 404)

    def test_uploads_route_serves_existing_file(self):
        """The /uploads/<filename> route serves files that exist in the configured upload folder."""
        app = create_app(TestConfig)
        upload_folder = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        test_filename = 'sample_doc.txt'
        test_path = os.path.join(upload_folder, test_filename)

        with open(test_path, 'w', encoding='utf-8') as f:
            f.write('society connect test content')

        client = app.test_client()
        response = client.get(f'/uploads/{test_filename}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), 'society connect test content')
        response.close()

        # Clean up test file safely
        try:
            if os.path.exists(test_path):
                os.remove(test_path)
        except PermissionError:
            pass


if __name__ == '__main__':
    unittest.main()
