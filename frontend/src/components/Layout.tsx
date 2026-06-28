import { NavLink } from 'react-router-dom'
import { BarChart2, Activity, Dumbbell, Settings, LogOut } from 'lucide-react'

const nav = [
  { to: '/',            label: 'Dashboard',    icon: BarChart2 },
  { to: '/measurements', label: 'Measurements', icon: Activity },
  { to: '/garmin',      label: 'Garmin Sync',  icon: Dumbbell },
  { to: '/profile',     label: 'Profile',      icon: Settings },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 bg-surface border-r border-border flex flex-col">
        <div className="px-5 py-6">
          <span className="text-primary font-bold text-lg tracking-tight">BodyComp</span>
        </div>

        <nav className="flex-1 px-3 space-y-1">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary/15 text-primary'
                    : 'text-muted hover:text-text hover:bg-border'
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 pb-5">
          <a
            href="/.auth/logout"
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted hover:text-danger hover:bg-border transition-colors w-full"
          >
            <LogOut size={17} />
            Sign out
          </a>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto p-6 bg-bg">
        {children}
      </main>
    </div>
  )
}
