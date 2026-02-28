import WebApp from '@twa-dev/sdk'

export type TelegramSession = {
  initData: string
  userId: number | null
}

export function initTelegram(): TelegramSession {
  WebApp.ready()
  WebApp.expand()

  return {
    initData: WebApp.initData || '',
    userId: WebApp.initDataUnsafe?.user?.id ?? null,
  }
}
