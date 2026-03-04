import WebApp from '@twa-dev/sdk'

export type TelegramSession = {
  initData: string
  userId: number | null
  initDataUnsafe: unknown
  platform: string
  version: string
}

export function initTelegram(): TelegramSession {
  WebApp.ready()
  WebApp.expand()

  return {
    initData: WebApp.initData || '',
    initDataUnsafe: WebApp.initDataUnsafe as unknown,
    platform: WebApp.platform,
    version: WebApp.version,
    userId: (WebApp.initDataUnsafe as any)?.user?.id ?? null,
  }
}