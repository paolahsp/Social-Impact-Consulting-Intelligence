export type RouteId =
  | 'new-diagnostic'
  | 'overview'
  | 'conversation'
  | 'next-steps'
  | 'brief'

export interface AppRouteDefinition {
  id: RouteId
  pathname: string
  title: string
  navigationLabel: string
  step: number
}

export const routeRegistry = [
  {
    id: 'new-diagnostic',
    pathname: '/new-diagnostic',
    title: 'Prepare your next client conversation',
    navigationLabel: 'New diagnostic',
    step: 1,
  },
  {
    id: 'overview',
    pathname: '/overview',
    title: 'Diagnostic overview',
    navigationLabel: 'Overview',
    step: 2,
  },
  {
    id: 'conversation',
    pathname: '/conversation',
    title: 'Prepare the conversation',
    navigationLabel: 'Conversation',
    step: 3,
  },
  {
    id: 'next-steps',
    pathname: '/next-steps',
    title: 'Recommended next steps',
    navigationLabel: 'Next steps',
    step: 4,
  },
  {
    id: 'brief',
    pathname: '/brief',
    title: 'Conversation brief',
    navigationLabel: 'Conversation brief',
    step: 5,
  },
] as const satisfies readonly AppRouteDefinition[]

export function getRouteByPath(pathname: string) {
  return routeRegistry.find((route) => route.pathname === pathname)
}
