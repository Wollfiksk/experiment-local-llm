# !!! Spusť na konci – smaže všechny lokální modely !!!
$ollama = ".\ollama.exe"

& $ollama rm kalendar-qwen
& $ollama rm kalendar-llama
& $ollama rm qwen2.5:3b
& $ollama rm llama3.2:3b

Write-Host "`nZbývající modely (seznam má být prázdný):"
& $ollama list
