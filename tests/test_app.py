import os
import tempfile
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    
    with app.test_client() as client:
        yield client
    
    # 清理临时文件夹
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER'], topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(app.config['UPLOAD_FOLDER'])

def test_index(client):
    """测试首页是否正常加载"""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Upload Files' in rv.data

def test_upload_no_file(client):
    """测试没有文件上传时的错误处理"""
    rv = client.post('/upload')
    assert rv.status_code == 400
    assert b'No file part' in rv.data

def test_upload_empty(client):
    """测试空文件列表的错误处理"""
    rv = client.post('/upload', data={
        'files': []
    })
    assert rv.status_code == 400
    assert b'No selected file' in rv.data
