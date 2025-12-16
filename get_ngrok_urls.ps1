$tunnels = Invoke-RestMethod -Uri http://127.0.0.1:4040/api/tunnels -ErrorAction SilentlyContinue
if (-not $tunnels) {
  Write-Warning "No ngrok API at 127.0.0.1:4040; make sure ngrok is running."
  exit 1
}

foreach ($t in $tunnels.tunnels) {
  "{0,-15} -> {1}" -f $t.name, $t.public_url
}
