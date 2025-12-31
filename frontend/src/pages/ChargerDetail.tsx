import { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Sidebar } from "@/components/layout/sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ArrowLeft, Loader2, BatteryCharging, History, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    LineChart,
    Line,
    Legend
} from "recharts";

interface ChargerDetail {
    id: string;
    vendor: string | null;
    model: string | null;
    is_online: boolean;
    parking_spot_label: string | null;
    connectors: { connector_id: number; status: string; current_transaction_id?: number }[];
}

interface Session {
    id: number;
    transaction_id: number;
    start_time: string;
    end_time: string | null;
    meter_start: number;
    meter_stop: number | null;
    total_energy: number | null;
    stop_reason: string | null;
    id_tag: string;
}

interface Log {
    id: number;
    timestamp: string;
    direction: string;
    message_type: string;
    action: string;
    payload: any;
}

interface Reading {
    timestamp: string;
    value: number;
    unit: string;
    measurand?: string;
    phase?: string;
    context?: string;
}

export default function ChargerDetail() {
    const { id } = useParams();
    const navigate = useNavigate();

    const [charger, setCharger] = useState<ChargerDetail | null>(null);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [logs, setLogs] = useState<Log[]>([]);
    const [loading, setLoading] = useState(true);

    // Modals
    const [selectedSession, setSelectedSession] = useState<Session | null>(null);
    const [sessionReadings, setSessionReadings] = useState<Reading[]>([]);
    const [readingsLoading, setReadingsLoading] = useState(false);
    const [showLogsModal, setShowLogsModal] = useState(false);

    useEffect(() => {
        if (!id) return;
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [id]);

    const fetchData = async () => {
        if (!id) return;
        try {
            const [resCharger, resSessions, resLogs] = await Promise.all([
                axios.get(`/api/admin/chargers/${id}`),
                axios.get(`/api/admin/chargers/${id}/sessions`),
                axios.get(`/api/admin/chargers/${id}/logs`)
            ]);
            setCharger(resCharger.data);
            setSessions(resSessions.data);
            setLogs(resLogs.data);
        } catch (error) {
            console.error("Error fetching charger details", error);
        } finally {
            setLoading(false);
        }
    };

    const openSessionModal = async (session: Session) => {
        setSelectedSession(session);
        setReadingsLoading(true);
        try {
            // Use session.transaction_id as per API
            const res = await axios.get(`/api/admin/sessions/${session.transaction_id}/readings`);
            setSessionReadings(res.data);
        } catch (error) {
            console.error("Error fetching readings", error);
        } finally {
            setReadingsLoading(false);
        }
    };

    const handleConnectorClick = (conn: { connector_id: number; status: string; current_transaction_id?: number }) => {
        if (conn.current_transaction_id) {
            // Find session object
            const session = sessions.find(s => s.transaction_id === conn.current_transaction_id);
            if (session) {
                openSessionModal(session);
            } else {
                // If not in list, open with minimal info to trigger fetch
                openSessionModal({
                    id: 0,
                    transaction_id: conn.current_transaction_id,
                    start_time: new Date().toISOString(),
                    end_time: null,
                    meter_start: 0,
                    meter_stop: null,
                    total_energy: 0,
                    stop_reason: null,
                    id_tag: "Unknown"
                });
            }
        }
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!charger) {
        return <div>Charger not found</div>;
    }

    // Connector 0 logic
    const connectorZero = charger.connectors.find(c => c.connector_id === 0);
    const visibleConnectors = charger.connectors.filter(c => c.connector_id !== 0);

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-8 bg-gray-50 dark:bg-gray-900 overflow-hidden h-screen flex flex-col">
                <div className="flex items-center gap-4 mb-6 shrink-0">
                    <button onClick={() => navigate("/")} className="p-2 hover:bg-gray-200 rounded-full">
                        <ArrowLeft className="h-5 w-5" />
                    </button>
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
                            {charger.id}
                            <span className={cn(
                                "text-sm px-2 py-1 rounded-full border border-current",
                                charger.is_online ? "text-green-600 bg-green-50" : "text-gray-500 bg-gray-50"
                            )}>
                                {charger.is_online ? "Online" : "Offline"}
                            </span>
                            {connectorZero && (
                                <span className={cn(
                                    "text-sm px-2 py-1 rounded-full border border-current",
                                    connectorZero.status === "Available" ? "text-green-600 bg-green-50" : "text-blue-600 bg-blue-50"
                                )}>
                                    Station Status: {connectorZero.status}
                                </span>
                            )}
                        </h2>
                        <p className="text-muted-foreground">
                            {charger.vendor} {charger.model} • {charger.parking_spot_label || "No Spot"}
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 shrink-0">
                    {visibleConnectors.map(conn => (
                        <Card
                            key={conn.connector_id}
                            className={cn(
                                "border-l-4 transition-all hover:shadow-md",
                                conn.current_transaction_id ? "cursor-pointer" : "",
                                conn.status === "Available" ? "border-l-green-500" :
                                    conn.status === "Charging" ? "border-l-blue-500" :
                                        conn.status === "Finishing" ? "border-l-blue-300" :
                                            conn.status === "Reserved" ? "border-l-orange-500" :
                                                conn.status === "Unavailable" || conn.status === "Faulted" ? "border-l-red-500" :
                                                    "border-l-gray-300"
                            )}
                            onClick={() => handleConnectorClick(conn)}
                        >
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Connector #{conn.connector_id}</CardTitle>
                                <BatteryCharging className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className={cn(
                                    "text-2xl font-bold",
                                    conn.status === "Available" ? "text-green-600" :
                                        conn.status === "Charging" ? "text-blue-600" :
                                            conn.status === "Faulted" ? "text-red-600" : "text-gray-700"
                                )}>{conn.status}</div>
                                <p className="text-xs text-muted-foreground">
                                    {conn.current_transaction_id ? "Click to view session" : "Status"}
                                </p>
                            </CardContent>
                        </Card>
                    ))}
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
                            <History className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{sessions.length}</div>
                            <p className="text-xs text-muted-foreground">Recorded sessions</p>
                        </CardContent>
                    </Card>
                    <Card
                        className="cursor-pointer hover:shadow-md transition-all border-l-4 border-l-purple-500"
                        onClick={() => setShowLogsModal(true)}
                    >
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">OCPP Logs</CardTitle>
                            <FileText className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{logs.length}</div>
                            <p className="text-xs text-muted-foreground">Click to view all logs</p>
                        </CardContent>
                    </Card>
                </div>

                <div className="grid grid-cols-1 gap-8 flex-1 min-h-0">
                    {/* Sessions List */}
                    <Card className="flex flex-col min-h-0">
                        <CardHeader className="shrink-0">
                            <CardTitle>Charging Sessions</CardTitle>
                            <CardDescription>Click on a session to view details</CardDescription>
                        </CardHeader>
                        <CardContent className="overflow-auto min-h-0">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Start Time</TableHead>
                                        <TableHead>Tx ID</TableHead>
                                        <TableHead>Energy (kWh)</TableHead>
                                        <TableHead>Status</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {sessions.map(s => (
                                        <TableRow
                                            key={s.id}
                                            className="cursor-pointer hover:bg-muted/50"
                                            onClick={() => openSessionModal(s)}
                                        >
                                            <TableCell className="text-xs whitespace-nowrap">
                                                {new Date(s.start_time).toLocaleString()}
                                            </TableCell>
                                            <TableCell className="font-mono text-xs">{s.transaction_id}</TableCell>
                                            <TableCell>
                                                {s.total_energy ? s.total_energy.toFixed(3) : "-"}
                                            </TableCell>
                                            <TableCell>
                                                {s.end_time ? (
                                                    <span className="text-xs bg-gray-100 text-gray-800 px-1 py-0.5 rounded">Finished</span>
                                                ) : (
                                                    <span className="text-xs bg-green-100 text-green-800 px-1 py-0.5 rounded animate-pulse">Active</span>
                                                )}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>


                </div>

                <Dialog open={!!selectedSession} onOpenChange={(open: boolean) => !open && setSelectedSession(null)}>
                    <DialogContent className="max-w-7xl h-[80vh] flex flex-col">
                        <DialogHeader>
                            <DialogTitle>Session Analysis - Tx #{selectedSession?.transaction_id}</DialogTitle>
                        </DialogHeader>
                        <div className="flex-1 w-full min-h-0">
                            {readingsLoading ? (
                                <div className="flex h-full items-center justify-center">
                                    <Loader2 className="h-8 w-8 animate-spin" />
                                </div>
                            ) : sessionReadings.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={sessionReadings}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                        <XAxis
                                            dataKey="timestamp"
                                            tickFormatter={(str: string) => new Date(str).toLocaleTimeString()}
                                            stroke="#888888"
                                            fontSize={12}
                                        />
                                        <YAxis
                                            stroke="#888888"
                                            fontSize={12}
                                            // Auto-scale Y axis
                                            domain={['auto', 'auto']}
                                        />
                                        <Tooltip
                                            labelFormatter={(str: string) => new Date(str).toLocaleString()}
                                            content={({ active, payload, label }: { active?: boolean, payload?: any[], label?: string }) => {
                                                if (active && payload && payload.length) {
                                                    return (
                                                        <div className="bg-white border rounded p-2 shadow-sm text-sm dark:bg-gray-800 dark:border-gray-700">
                                                            <p className="font-semibold mb-1">{label ? new Date(label).toLocaleString() : ''}</p>
                                                            {payload.map((entry: any, index: number) => (
                                                                <div key={index} className="flex items-center gap-2" style={{ color: entry.color }}>
                                                                    <span>{entry.name}:</span>
                                                                    <span className="font-mono">{entry.value.toFixed(2)}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    );
                                                }
                                                return null;
                                            }}
                                        />
                                        <Legend />
                                        {/* Dynamically generate lines for each series */}
                                        {(() => {
                                            // Group data by Series Key: Measurand + Phase + Context
                                            // Recharts needs an array of objects where each object is a timestamp point
                                            // But here our API returns a flat list where each row is one reading.
                                            // Since we use 'value' as dataKey, we might need multiple passes or simple filtering if we want to use the simpler API.

                                            // Actually, the simplest way with loose data in Recharts is to filter the data for the specific line 
                                            // provided that we don't strictly align X-axis points (connectNulls helps). 
                                            // However, proper way is to pivot data if timestamps align, or just render multiple lines 
                                            // each filtering the main dataset? No, Recharts 'data' prop is global.

                                            // Better approach: We transform the flat list into unique Series on the fly.
                                            const seriesMap = new Map<string, Reading[]>();
                                            sessionReadings.forEach(r => {
                                                const key = [r.measurand, r.phase, r.unit].filter(Boolean).join(" - ") || "Value";
                                                if (!seriesMap.has(key)) seriesMap.set(key, []);
                                                seriesMap.get(key)!.push(r);
                                            });

                                            const colors = ["#2563eb", "#dc2626", "#16a34a", "#ca8a04", "#9333ea", "#0891b2"];

                                            return Array.from(seriesMap.entries()).map(([key, data], index) => (
                                                <Line
                                                    key={key}
                                                    data={data} // Override data for this specific line
                                                    type="monotone"
                                                    dataKey="value"
                                                    name={key}
                                                    stroke={colors[index % colors.length]}
                                                    dot={false}
                                                    strokeWidth={2}
                                                    connectNulls={true}
                                                />
                                            ));
                                        })()}
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex h-full items-center justify-center text-muted-foreground">
                                    No meter readings available for graph.
                                </div>
                            )}
                        </div>
                    </DialogContent>
                </Dialog>

                {/* Logs Modal */}
                <Dialog open={showLogsModal} onOpenChange={setShowLogsModal}>
                    <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
                        <DialogHeader>
                            <DialogTitle>OCPP Logs</DialogTitle>
                        </DialogHeader>
                        <div className="flex-1 overflow-auto bg-muted/20 p-2 rounded border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-[100px]">Time</TableHead>
                                        <TableHead>Dir</TableHead>
                                        <TableHead>Action</TableHead>
                                        <TableHead>Payload</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {logs.map(log => (
                                        <TableRow key={log.id}>
                                            <TableCell className="text-xs whitespace-nowrap text-muted-foreground">
                                                {new Date(log.timestamp).toLocaleTimeString()}
                                            </TableCell>
                                            <TableCell>
                                                {log.direction === "Incoming" ? (
                                                    <span className="text-xs font-bold text-blue-600">IN</span>
                                                ) : (
                                                    <span className="text-xs font-bold text-orange-600">OUT</span>
                                                )}
                                            </TableCell>
                                            <TableCell className="text-xs font-medium">{log.action}</TableCell>
                                            <TableCell className="text-xs font-mono max-w-[300px] break-all">
                                                {JSON.stringify(log.payload)}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </DialogContent>
                </Dialog>
            </main>
        </div>
    );
}
