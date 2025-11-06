# Minimal deployment script
import os
import shutil

# Create minimal deployment folder
if os.path.exists('deploy_minimal'):
    shutil.rmtree('deploy_minimal')

os.makedirs('deploy_minimal')

# Copy essential files only
essential_files = [
    'app.py',
    'blockchain.py', 
    'face_utils.py',
    'requirements.txt',
    'railway.toml',
    '.railwayignore'
]

essential_folders = [
    'templates',
    'static/js',
    'static/css',
    'routes',
    'utils'
]

# Copy files
for file in essential_files:
    if os.path.exists(file):
        shutil.copy2(file, 'deploy_minimal/')

# Copy folders
for folder in essential_folders:
    if os.path.exists(folder):
        shutil.copytree(folder, f'deploy_minimal/{folder}', dirs_exist_ok=True)

# Create empty directories for uploads
os.makedirs('deploy_minimal/static/uploads', exist_ok=True)
os.makedirs('deploy_minimal/static/protocard', exist_ok=True)

print("✅ Minimal deployment folder created!")
print("📁 Deploy from: deploy_minimal/")