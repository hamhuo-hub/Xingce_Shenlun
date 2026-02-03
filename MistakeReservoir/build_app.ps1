Write-Host "Installing dependencies..."
pip install -r requirements.txt

Write-Host "Building Executable..."
# --onedir: Folder output (faster start, external data friendly)
# --console: Show terminal window (useful for server logs)
# --add-data: Bundle static files
pyinstaller --noconfirm --onedir --console --name MistakeReservoir --add-data "static;static" main.py

Write-Host "Copying User Data..."
Copy-Item -Path "reservoir.db" -Destination "dist/MistakeReservoir/" -Force
Copy-Item -Path "media" -Destination "dist/MistakeReservoir/" -Recurse -Force
Copy-Item -Path "uploads" -Destination "dist/MistakeReservoir/" -Recurse -Force

Write-Host "Build Complete!"
Write-Host "You can find your app in: dist\MistakeReservoir\MistakeReservoir.exe"
