import os
import shutil
import tempfile
import zipfile

EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git", "__pycache__", "venv"}
EXCLUDE_FILES = {"package-lock.json", "desktop"}

FILES_TO_DEPLOY = [
    "backend/app.py",
    "backend/config.py",
    "backend/requirements.txt",
    "backend/bot/",
    "backend/database/",
    "backend/game_logic/",
    "backend/ai/",
    ".env.example",
]


def create_deployment_zip(output_path="penthouse_dream_deploy.zip"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = tempfile.mkdtemp()
    deploy_dir = os.path.join(temp_dir, "penthouse-dream")
    os.makedirs(deploy_dir)

    backend_dir = os.path.join(deploy_dir, "backend")
    shutil.copytree(os.path.join(base_dir, "backend"), backend_dir,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "venv"))

    startup_script = os.path.join(deploy_dir, "run_bot.py")
    with open(startup_script, "w") as f:
        f.write('''import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(BASE, "backend")
os.chdir(BACKEND)
sys.path.insert(0, BACKEND)

import asyncio
from bot.main import main
asyncio.run(main())
''')

    readme = os.path.join(deploy_dir, "README_PYTHONANYWHERE.md")
    with open(readme, "w") as f:
        f.write("""# Deploy on PythonAnywhere

## 1. Upload
- Create account on pythonanywhere.com
- Open Files tab
- Upload this zip
- Open Bash console and run:
  ```
  unzip penthouse_dream_deploy.zip
  cd penthouse-dream
  ```

## 2. Virtualenv
```
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

## 3. Token
```
echo 'BOT_TOKEN=your_token_here' > .env
echo 'DB_TYPE=sqlite' >> .env
```

## 4. Run
```
python run_bot.py
```

## 5. Always-on task
Go to Tasks tab -> Always-on task -> Add:
```
source /home/YOUR_USER/penthouse-dream/venv/bin/activate && python /home/YOUR_USER/penthouse-dream/run_bot.py
```
""")

    zip_path = os.path.join(base_dir, output_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(deploy_dir):
            rel_root = os.path.relpath(root, temp_dir)
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join(rel_root, file)
                zf.write(file_path, arcname)

    shutil.rmtree(temp_dir)
    print(f"Deployment package created: {zip_path}")
    print(f"Size: {os.path.getsize(zip_path) / 1024:.1f} KB")
    return zip_path


if __name__ == "__main__":
    create_deployment_zip()
