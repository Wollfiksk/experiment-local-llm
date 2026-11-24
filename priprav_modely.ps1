# Stáhne oba modely a vytvoří z nich upravené verze podle Modelfile.
# Spouštěj ve složce s ollama.exe (server musí běžet v jiném okně).
$ollama = ".\ollama.exe"

& $ollama pull qwen2.5:3b
& $ollama pull llama3.2:3b

& $ollama create kalendar-qwen  -f Modelfile-qwen
& $ollama create kalendar-llama -f Modelfile-llama

& $ollama list
