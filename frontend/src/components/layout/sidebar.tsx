import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { LayoutDashboard, LogOut, Users, UserCircle, MapPin, Settings } from "lucide-react";
import { useAuth } from "@/providers/auth-provider";
import { Button } from "@/components/ui/button";

export function Sidebar() {
    const location = useLocation();
    const { user, logout } = useAuth();

    const navItems = [
        {
            title: "Dashboard",
            href: "/",
            icon: LayoutDashboard,
        },
        {
            title: "Renters",
            href: "/renters",
            icon: UserCircle,
        },
        {
            title: "Parking Spots",
            href: "/parking-spots",
            icon: MapPin,
        },
    ];

    return (
        <div className="flex h-screen w-64 flex-col border-r bg-gray-100/40 dark:bg-gray-800/40">
            <div className="p-6">
                <h1 className="text-xl font-bold tracking-tight">Onetime Admin</h1>
            </div>
            <div className="flex-1 px-4 space-y-2">
                {navItems.map((item) => (
                    <Link
                        key={item.href}
                        to={item.href}
                        className={cn(
                            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:text-primary",
                            location.pathname === item.href
                                ? "bg-gray-200 text-primary dark:bg-gray-800"
                                : "text-muted-foreground hover:bg-gray-200 dark:hover:bg-gray-800"
                        )}
                    >
                        <item.icon className="h-4 w-4" />
                        {item.title}
                    </Link>
                ))}
            </div>
            <div className="p-4 border-t space-y-4">
                <div className="flex items-center justify-between px-2">
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                            <Users className="h-4 w-4 text-primary" />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-sm font-medium">{user?.username}</span>
                            <span className="text-xs text-muted-foreground capitalize">{user?.role}</span>
                        </div>
                    </div>
                    <Link to="/users">
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Settings className="h-4 w-4" />
                        </Button>
                    </Link>
                </div>
                <Button
                    variant="ghost"
                    className="w-full justify-start gap-2 text-red-500 hover:bg-red-50 hover:text-red-600"
                    onClick={logout}
                >
                    <LogOut className="h-4 w-4" />
                    Logout
                </Button>
            </div>
        </div>
    );
}
