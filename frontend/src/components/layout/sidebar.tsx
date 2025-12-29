import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { LayoutDashboard, LogOut } from "lucide-react";
import { useAuth } from "@/providers/auth-provider";
import { Button } from "@/components/ui/button";

export function Sidebar() {
    const location = useLocation();
    const { logout } = useAuth();

    const navItems = [
        {
            title: "Dashboard",
            href: "/",
            icon: LayoutDashboard,
        },
        // Add more items here later (Chargers, Renters)
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
            <div className="p-4 border-t">
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
