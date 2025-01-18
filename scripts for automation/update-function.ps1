$cliCheck = Get-Command yc -ErrorAction SilentlyContinue

if (-not $cliCheck) {
    Write-Host "Yandex CLI не установлен"
    exit
}

yc serverless function version create `
  --function-id "d4eeil96knbv8vqnbrg4" `
  --service-account-id ajeputjohm1o4rda7sh2 `
  --runtime python312 `
  --entrypoint guestbook-backend.handler `
  --memory 128m `
  --execution-timeout 5s `
  --source-path "../backend/" `
  --folder-id "b1g0nsi0ers294rrqklf" `

Write-Host "Новая версия функции успешно загружена"