import WebApp from '@twa-dev/sdk'

export type TelegramSession = {
  initData: string
  userId: number | null
}

export function initTelegram(): TelegramSession {
  WebApp.ready()
  WebApp.expand()

  return {
     initData: WebApp.initData,           // string (what backend needs)
    initDataUnsafe: WebApp.initDataUnsafe,
    platform: WebApp.platform,
    version: WebApp.version,
    userId: WebApp.initDataUnsafe?.user?.id ?? null,
  }
}
