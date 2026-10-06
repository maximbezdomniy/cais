# Script to build Flet app to .exe

Write-Host "Installing dependencies..."
py -m pip install -r requirements.txt

Write-Host "Building application..."
$ScriptsPath = py -c "import sysconfig; print(sysconfig.get_path('scripts'))"
& "$ScriptsPath\flet.exe" pack main.py --name "GigaChatClient" --add-data "assets;assets"

Write-Host "Build finished. The executable is located in the dist folder."
