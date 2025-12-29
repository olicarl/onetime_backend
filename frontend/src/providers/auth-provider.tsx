import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import axios from "axios";

interface User {
    username: string;
    role: string;
    mode: string;
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    login: (creds: any) => Promise<void>;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const checkAuth = async () => {
        try {
            const res = await axios.get("/api/me");
            setUser(res.data);
        } catch {
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        checkAuth();
    }, []);

    const login = async (creds: any) => {
        await axios.post("/api/login", creds);
        await checkAuth();
    };

    const logout = async () => {
        await axios.post("/api/logout");
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
