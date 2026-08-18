import { useEffect, useRef } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useDiagnostic } from '../../app/diagnosticContext'
import { getRouteByPath, routeRegistry } from '../../app/routeRegistry'
import { Brand } from './Brand'

function SharedHeader() {
  const { briefExists, isDemoMode, resetDiagnostic, result } = useDiagnostic()
  const location = useLocation()
  const currentRoute = getRouteByPath(location.pathname) ?? routeRegistry[0]

  return (
    <header className="border-b border-border bg-canvas">
      <div className="mx-auto w-full max-w-content px-page py-3">
        <div className="flex min-h-14 flex-wrap items-center justify-between gap-x-6 gap-y-2">
          <div className="flex min-w-0 items-center gap-3">
            <Brand compact />
            {isDemoMode && <><span
              aria-describedby="demo-description"
              className="rounded-control bg-blush px-2.5 py-1 text-xs font-semibold text-ink"
            >
              Demo
            </span>
            <span className="sr-only" id="demo-description">
              Uses sample material. Nothing is sent or permanently saved.
            </span></>}
          </div>

          <p className="text-sm font-semibold text-ink lg:hidden">
            Step {currentRoute.step} of {routeRegistry.length}
          </p>

          <nav aria-label="Diagnostic progress" className="hidden lg:block">
            <ol className="flex items-center gap-1">
              {routeRegistry.map((route) => (
                <li key={route.id}>
                  {(route.step > 1 && !result) || (route.id === 'brief' && !briefExists) ? (
                    <span aria-disabled="true" className="inline-flex min-h-11 items-center border-b-2 border-transparent px-3 text-sm font-semibold text-muted/60">
                      <span className="mr-2 text-xs">{route.step}</span>
                      {route.navigationLabel}
                    </span>
                  ) : (
                    <NavLink
                      className={({ isActive }) =>
                        `inline-flex min-h-11 items-center border-b-2 px-3 text-sm font-semibold transition-colors ${
                          isActive
                            ? 'border-accent text-ink'
                            : 'border-transparent text-muted hover:text-ink'
                        }`
                      }
                      to={route.pathname}
                      onClick={route.id === 'new-diagnostic' ? resetDiagnostic : undefined}
                    >
                      <span className="mr-2 text-xs text-muted">{route.step}</span>
                      {route.id === 'brief' && briefExists ? 'Current brief' : route.navigationLabel}
                    </NavLink>
                  )}
                </li>
              ))}
            </ol>
          </nav>
        </div>
      </div>
    </header>
  )
}

export function AppShell() {
  const location = useLocation()
  const previousPath = useRef(location.pathname)

  useEffect(() => {
    if (previousPath.current !== location.pathname) {
      document.getElementById('main-content')?.focus({ preventScroll: true })
      previousPath.current = location.pathname
    }
  }, [location.pathname])

  const focusMainContent = () => {
    document.getElementById('main-content')?.focus({ preventScroll: true })
  }

  return (
    <>
      <a className="skip-link" href="#main-content" onClick={focusMainContent}>
        Skip to main content
      </a>
      <div className="min-h-screen">
        <SharedHeader />
        <main
          className="main-content-target min-w-0"
          id="main-content"
          tabIndex={-1}
        >
          <Outlet />
        </main>
      </div>
    </>
  )
}
