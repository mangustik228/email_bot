<!-- deployer:start -->
## Деплой (управляется через `deployer`)

Этот сервис провижнится и деплоится через **deployer** — локальную CLI (не запускается в CI).

- Секреты GitHub Actions `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY` и переменная
  `PROJECT_DIR` заводятся и ротируются утилитой deployer — **руками не трогать**.
- На сервере сервис работает под юзером `email_bot` из `/opt/email_bot`.
- Модель деплоя: `appleboy/ssh-action` заходит по SSH и делает `git pull` на сервере
  (два отдельных ключа — read-only deploy key для git и SSH-ключ Actions для сервера).
- Диагностика CI прямо из терминала, без браузера:
  `deployer ci logs --repo email_bot` (последний упавший прогон) и
  `deployer ci status --repo email_bot`.
- Ротация SSH-ключа Actions: `deployer rotate-key --repo email_bot`.
<!-- deployer:end -->
