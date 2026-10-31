import type { ReactNode } from 'react'
import { useT } from '../i18n'

/** Text produced by the backend or the AI, shown as received. Isolated as LTR English inside an RTL page. */
export function Orig({ children }: { children: ReactNode }) {
  const { lang } = useT()
  if (lang === 'en') return <>{children}</>
  return (
    <span lang="en" dir="ltr" className="orig">
      {children}
    </span>
  )
}
