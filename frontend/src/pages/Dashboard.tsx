import { useEffect, useState } from "react";
import axios from "axios";
import { cn } from "@/lib/utils";
import { Sidebar } from "@/components/layout/sidebar";
import { useNavigate } from "react-router-dom";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2, Power, PowerOff } from "lucide-react";

interface Charger {
    id: string;
    vendor: string | null;
    model: string | null;
    is_online: boolean;
    parking_spot_label: string | null;
    connectors: { connector_id: number; status: string }[];
    active_session: { transaction_id: number; renter_name: string; energy_consumed: number } | null;
}

export default function Dashboard() {
    const [chargers, setChargers] = useState<Charger[]>([]);
    const [loading, setLoading] = useState(true);
    const [serverIp, setServerIp] = useState<string>(window.location.hostname);
    const navigate = useNavigate();

    useEffect(() => {
        fetchChargers();
        fetchSystemInfo();
        // Poll every 10 seconds
        const interval = setInterval(fetchChargers, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchSystemInfo = async () => {
        try {
            const res = await axios.get("/api/admin/system-info");
            if (res.data.ip_address) {
                setServerIp(res.data.ip_address);
            }
        } catch (error) {
            console.error("Failed to fetch system info", error);
        }
    };

    const fetchChargers = async () => {
        try {
            const res = await axios.get("/api/admin/chargers");
            setChargers(res.data);
        } catch (error) {
            console.error("Failed to fetch chargers", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-8 bg-gray-50 dark:bg-gray-900">
                <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold tracking-tight">Chargers</h2>
                </div>

                <Card className="mb-8 border-l-4 border-l-blue-500 shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            Installer Configuration
                        </CardTitle>
                        <CardDescription>
                            Use the following WebSocket URL to connect new charging stations.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-4 p-4 bg-muted rounded-md border">
                            <code className="flex-1 font-mono text-sm">
                                ws://{serverIp}:8000/ocpp/&lt;CHARGE_POINT_ID&gt;
                            </code>
                            <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                                WebSocket URL
                            </span>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Charging Stations</CardTitle>
                        <CardDescription>Overview of all connected chargers</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="flex justify-center p-8">
                                <Loader2 className="h-8 w-8 animate-spin" />
                            </div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Status</TableHead>
                                        <TableHead>ID</TableHead>
                                        <TableHead>Spot</TableHead>
                                        <TableHead>Renter (Active)</TableHead>
                                        <TableHead>Energy</TableHead>
                                        <TableHead>Connectors</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {chargers.map((c) => (
                                        <TableRow
                                            key={c.id}
                                            className="cursor-pointer hover:bg-muted/50 transition-colors"
                                            onClick={() => navigate(`/chargers/${c.id}`)}
                                        >
                                            <TableCell>
                                                <div className="flex items-center gap-2">
                                                    {c.is_online ? <Power className="h-4 w-4 text-green-500" /> : <PowerOff className="h-4 w-4 text-gray-400" />}
                                                    <span className={c.is_online ? "text-green-600 font-medium" : "text-gray-500"}>
                                                        {c.is_online ? "Online" : "Offline"}
                                                    </span>
                                                </div>
                                            </TableCell>
                                            <TableCell className="font-mono text-xs">{c.id}</TableCell>
                                            <TableCell>{c.parking_spot_label || "-"}</TableCell>
                                            <TableCell>
                                                {c.active_session ? (
                                                    <span className="font-semibold text-blue-600">
                                                        {c.active_session.renter_name}
                                                    </span>
                                                ) : (
                                                    <span className="text-muted-foreground">-</span>
                                                )}
                                            </TableCell>
                                            <TableCell>
                                                {c.active_session ? `${c.active_session.energy_consumed} Wh` : "-"}
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex gap-2">
                                                    {c.connectors.map((conn) => (
                                                        <span
                                                            key={conn.connector_id}
                                                            className={cn(
                                                                "px-2 py-1 rounded text-xs font-medium border",
                                                                conn.status === "Available"
                                                                    ? "bg-green-100 text-green-800 border-green-200"
                                                                    : conn.status === "Charging"
                                                                        ? "bg-blue-100 text-blue-800 border-blue-200"
                                                                        : "bg-gray-100 text-gray-800 border-gray-200"
                                                            )}
                                                        >
                                                            #{conn.connector_id}: {conn.status}
                                                        </span>
                                                    ))}
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                    {chargers.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                                                No chargers found. Connect a charger to see it here.
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
