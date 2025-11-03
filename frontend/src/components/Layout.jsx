import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  LayoutDashboard, 
  Upload, 
  Users, 
  BarChart3,
  Shield,
  LogOut,
  Menu,
  X,
  Activity,
  Sparkles
} from 'lucide-react';
import { useState } from 'react';

function Layout() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Failed to logout:', error);
    }
  };

  const navigation = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Upload', path: '/upload', icon: Upload },
    { name: 'Patients', path: '/patients', icon: Users },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Compliance', path: '/compliance', icon: Shield },
  ];

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-gray-50">
      {/* Top Navigation - Modern Design */}
      <nav className="bg-white/95 backdrop-blur-lg shadow-lg border-b border-blue-100/50 sticky top-0 z-50">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo Section - Compact */}
            <div className="flex items-center min-w-0">
              <Link to="/" className="flex-shrink-0 flex items-center gap-2 group">
                {/* Enhanced Logo Icon */}
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-xl blur-md opacity-50 group-hover:opacity-75 transition-opacity"></div>
                  <div className="relative inline-flex items-center justify-center w-10 h-10 bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <Activity className="w-5 h-5 text-white animate-pulse" strokeWidth={2.5} />
                  </div>
                </div>
                {/* Enhanced Logo Text */}
                <div className="hidden sm:block">
                  <div className="flex items-center gap-1.5">
                    <h1 className="text-lg font-black bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent leading-tight whitespace-nowrap">
                      MediScan AI
                    </h1>
                    <Sparkles className="w-3.5 h-3.5 text-yellow-500 animate-pulse" />
                  </div>
                  <p className="text-xs font-medium text-gray-500 hidden xl:block tracking-wide whitespace-nowrap">
                    🏥 Advanced Medical Intelligence
                  </p>
                </div>
              </Link>
            </div>

            {/* Desktop Navigation - Compact */}
            <div className="hidden md:flex items-center gap-1 flex-1 justify-center max-w-2xl mx-4">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`group relative flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-200 whitespace-nowrap ${
                      active
                        ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-md'
                        : 'text-gray-700 hover:bg-blue-50 hover:text-blue-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>

            {/* User Menu - Compact */}
            <div className="flex items-center gap-2">
              {/* Real-Time Badge - Compact */}
              <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-full shadow-sm">
                <div className="relative">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-ping absolute"></div>
                  <div className="w-2 h-2 bg-green-500 rounded-full relative"></div>
                </div>
                <span className="text-xs font-bold text-green-700">LIVE</span>
              </div>

              {/* User Profile - Compact */}
              <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-center w-7 h-7 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full text-white text-xs font-bold">
                  {currentUser?.email?.[0]?.toUpperCase() || 'U'}
                </div>
                <div className="text-xs">
                  <div className="font-semibold text-gray-900 max-w-[120px] truncate">
                    {currentUser?.email?.split('@')[0] || 'User'}
                  </div>
                  <div className="text-[10px] text-gray-500">Online</div>
                </div>
              </div>

              {/* Logout Button - Compact */}
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-white bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 rounded-lg shadow-md hover:shadow-lg transition-all duration-200"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden xl:inline">Logout</span>
              </button>

              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-lg text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-all"
              >
                {mobileMenuOpen ? (
                  <X className="w-5 h-5" />
                ) : (
                  <Menu className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation - Enhanced */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-blue-100 bg-gradient-to-b from-white to-blue-50/30 backdrop-blur-lg">
            <div className="px-3 pt-3 pb-4 space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center px-4 py-3 rounded-xl text-base font-semibold transition-all duration-300 ${
                      active
                        ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg'
                        : 'text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 hover:text-blue-700'
                    }`}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </Link>
                );
              })}
              
              {/* Mobile User Info */}
              <div className="pt-3 mt-3 border-t border-gray-200">
                <div className="flex items-center gap-3 px-4 py-2 bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl">
                  <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full text-white text-sm font-bold">
                    {currentUser?.email?.[0]?.toUpperCase() || 'U'}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-900">{currentUser?.email}</div>
                    <div className="text-xs text-gray-500">Online • Mobile</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;

