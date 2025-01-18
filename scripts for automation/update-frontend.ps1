$cliCheck = Get-Command yc -ErrorAction SilentlyContinue

if (-not $cliCheck) {
    Write-Host "Yandex CLI не установлен"
    exit
}

yc storage s3api put-object `
  --body "../frontend/index.html" `
  --bucket "guestbook-frontend" `
  --key "index.html" `
  --folder-id "b1g0nsi0ers294rrqklf"

Write-Host "Файл успешно загружен"