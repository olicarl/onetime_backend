import { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Sidebar } from "@/components/layout/sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ArrowLeft, Loader2, BatteryCharging, History as HistoryIcon, FileText, PlugZap, Heart, ArrowDown } from "lucide-react";
import { cn } from "@/lib/utils";
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    LineChart,
    Line,
    Legend,
    Brush
} from "recharts";

interface ChargerDetail {
    id: string;
    vendor: string | null;
    model: string | null;
    is_online: boolean;
    kiosk_mode: boolean;
    last_heartbeat?: string | null;
    last_seen?: string | null;
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
    renter_name?: string | null;
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
function parseServerDate(dateString: string | null | undefined): Date | null {
    if (!dateString) return null;
    // If the string doesn't end with Z or have an offset, assume it is UTC
    const hasTimezone = dateString.endsWith('Z') || /[+-]\d{2}:?\d{2}$/.test(dateString);
    return new Date(hasTimezone ? dateString : dateString + 'Z');
}

function formatTimeAgo(dateString: string | null | undefined): string {
    const date = parseServerDate(dateString);
    if (!date) return "No heartbeat";
    const now = new Date();
    const diffInSeconds = Math.floor((date.getTime() - now.getTime()) / 1000);
    
    // Fallback logic for basic browsers if Intl.RelativeTimeFormat is not supported, 
    // but it is in modern browsers.
    const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
    
    const absDiff = Math.abs(diffInSeconds);
    if (absDiff < 60) return rtf.format(Math.sign(diffInSeconds) * absDiff, 'second');
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    const absDiffMin = Math.abs(diffInMinutes);
    if (absDiffMin < 60) return rtf.format(Math.sign(diffInMinutes) * absDiffMin, 'minute');
    const diffInHours = Math.floor(diffInMinutes / 60);
    const absDiffHours = Math.abs(diffInHours);
    if (absDiffHours < 24) return rtf.format(Math.sign(diffInHours) * absDiffHours, 'hour');
    const diffInDays = Math.floor(diffInHours / 24);
    return rtf.format(Math.sign(diffInDays) * Math.abs(diffInDays), 'day');
}

function formatDuration(start: string, end: string | null): string {
    const startDate = parseServerDate(start);
    const endDate = end ? parseServerDate(end) : new Date();
    
    if (!startDate || !endDate) return "-";
    
    const startTime = startDate.getTime();
    const endTime = endDate.getTime();
    const diffInSeconds = Math.floor((endTime - startTime) / 1000);

    const hours = Math.floor(diffInSeconds / 3600);
    const minutes = Math.floor((diffInSeconds % 3600) / 60);
    const seconds = diffInSeconds % 60;

    const parts = [];
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0 || hours > 0) parts.push(`${minutes}m`);
    parts.push(`${seconds}s`);

    return parts.join(' ');
}

export default function ChargerDetail() {
    const { id } = useParams();
    const navigate = useNavigate();

    const [charger, setCharger] = useState<ChargerDetail | null>(null);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [logs, setLogs] = useState<Log[]>([]);
    const [loading, setLoading] = useState(true);
    const [stoppingSessionId, setStoppingSessionId] = useState<number | null>(null);

    // Modals
    const [selectedSession, setSelectedSession] = useState<Session | null>(null);
    const [sessionReadings, setSessionReadings] = useState<Reading[]>([]);
    const [readingsLoading, setReadingsLoading] = useState(false);
    const [showLogsModal, setShowLogsModal] = useState(false);
    const [hiddenSeries, setHiddenSeries] = useState<Record<string, boolean>>({});
    const [selectedLogDate, setSelectedLogDate] = useState(() => {
        const today = new Date();
        return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    });

    useEffect(() => {
        if (!id) return;
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [id]);

    const fetchData = async () => {
        if (!id) return;
        try {
            const [resCharger, resSessions] = await Promise.all([
                axios.get(`/api/admin/chargers/${id}`),
                axios.get(`/api/admin/chargers/${id}/sessions`)
            ]);
            setCharger(resCharger.data);
            setSessions(resSessions.data);
        } catch (error) {
            console.error("Error fetching charger details", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchLogs = async (date: string) => {
        if (!id) return;
        try {
            const res = await axios.get(`/api/admin/chargers/${id}/logs?date=${date}`);
            setLogs(res.data);
        } catch (error) {
            console.error("Error fetching logs", error);
        }
    };

    useEffect(() => {
        if (showLogsModal && id) {
            fetchLogs(selectedLogDate);
        }
    }, [showLogsModal, selectedLogDate, id]);

    const toggleKioskMode = async () => {
        if (!charger) return;
        try {
            const newMode = !charger.kiosk_mode;
            await axios.put(`/api/admin/chargers/${charger.id}`, { kiosk_mode: newMode });
            setCharger({ ...charger, kiosk_mode: newMode });
        } catch (error) {
            console.error("Error toggling kiosk mode", error);
        }
    };

    const openSessionModal = async (session: Session) => {
        setSelectedSession(session);
        setReadingsLoading(true);
        setHiddenSeries({});
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

    const handleRemoteStop = async (e: React.MouseEvent, transactionId: number) => {
        e.stopPropagation();
        if (!charger) return;
        
        if (!confirm(`Are you sure you want to stop transaction #${transactionId}?`)) {
            return;
        }

        setStoppingSessionId(transactionId);
        try {
            await axios.post(`/api/admin/chargers/${charger.id}/remote-stop`, {
                transaction_id: transactionId
            });
            alert("Remote stop command accepted");
            fetchData();
        } catch (error: any) {
            console.error("Remote stop failed", error);
            alert(error.response?.data?.detail || "Failed to remote stop charging session");
        } finally {
            setStoppingSessionId(null);
        }
    };

    const handleLegendClick = (e: any) => {
        const seriesName = e.dataKey;
        setHiddenSeries(prev => ({
            ...prev,
            [seriesName]: !prev[seriesName]
        }));
    };

    const chartDataMemo = useMemo(() => {
        const pivotedDataMap = new Map<string, any>();
        const unitsMap = new Set<string>();
        const seriesUnitMap = new Map<string, string>();

        sessionReadings.forEach(r => {
            const keyParts = [r.measurand, r.phase].filter(Boolean);
            const key = keyParts.length > 0 ? keyParts.join(" - ") : "Value";
            
            const seriesKey = r.unit ? `${key} (${r.unit})` : key;
            const unit = r.unit || 'default';
            
            unitsMap.add(unit);
            seriesUnitMap.set(seriesKey, unit);

            if (!pivotedDataMap.has(r.timestamp)) {
                pivotedDataMap.set(r.timestamp, { timestamp: r.timestamp });
            }
            const dataPoint = pivotedDataMap.get(r.timestamp);
            dataPoint[seriesKey] = r.value;
        });

        const chartData = Array.from(pivotedDataMap.values()).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        const uniqueUnits = Array.from(unitsMap);
        if (uniqueUnits.length === 0) uniqueUnits.push('default');
        
        return { chartData, uniqueUnits, seriesUnitMap };
    }, [sessionReadings]);

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
                    id_tag: "Unknown",
                    renter_name: "Unknown"
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
                        <div className="flex items-center gap-4 text-muted-foreground mt-1">
                            <span>{charger.vendor} {charger.model} • {charger.parking_spot_label || "No Spot"}</span>
                            <div className="flex items-center gap-2">
                                <label htmlFor="kiosk-mode" className="text-sm font-medium">Kiosk Mode (Free Vend)</label>
                                <div
                                    className={cn("w-10 h-5 rounded-full peer cursor-pointer transition-colors relative", charger.kiosk_mode ? "bg-green-500" : "bg-gray-300")}
                                    onClick={toggleKioskMode}
                                >
                                    <div className={cn("absolute top-0.5 left-0.5 bg-white w-4 h-4 rounded-full transition-transform", charger.kiosk_mode ? "translate-x-5" : "translate-x-0")}></div>
                                </div>
                            </div>
                        </div>
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
                            <HistoryIcon className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{sessions.length}</div>
                            <p className="text-xs text-muted-foreground">Recorded sessions</p>
                        </CardContent>
                    </Card>
                    <Card
                        className="cursor-pointer hover:shadow-md transition-all border-l-4 border-l-purple-500 flex flex-col justify-between"
                        onClick={() => setShowLogsModal(true)}
                    >
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">OCPP Logs</CardTitle>
                            <FileText className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent className="space-y-2">
                            <div className="flex items-center gap-2">
                                <Heart className="h-4 w-4 text-red-500" />
                                <span className="text-sm font-bold">{formatTimeAgo(charger.last_heartbeat)}</span>
                                <span className="text-[10px] text-muted-foreground uppercase">Heartbeat</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <ArrowDown className="h-4 w-4 text-blue-500" />
                                <span className="text-sm font-bold">{formatTimeAgo(charger.last_seen)}</span>
                                <span className="text-[10px] text-muted-foreground uppercase">Last Activity</span>
                            </div>
                            <p className="text-[10px] text-muted-foreground mt-2 italic">Click to view logs</p>
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
                                        <TableHead>End Time</TableHead>
                                        <TableHead>Duration</TableHead>
                                        <TableHead>Tx ID</TableHead>
                                        <TableHead>Energy (kWh)</TableHead>
                                        <TableHead>Renter</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
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
                                                {parseServerDate(s.start_time)?.toLocaleString("de-CH")}
                                            </TableCell>
                                            <TableCell className="text-xs whitespace-nowrap">
                                                {s.end_time ? parseServerDate(s.end_time)?.toLocaleString("de-CH") : "-"}
                                            </TableCell>
                                            <TableCell className="text-xs whitespace-nowrap">
                                                {formatDuration(s.start_time, s.end_time)}
                                            </TableCell>
                                            <TableCell className="font-mono text-xs">{s.transaction_id}</TableCell>
                                            <TableCell>
                                                {s.total_energy ? s.total_energy.toFixed(3) : "-"}
                                            </TableCell>
                                            <TableCell className="text-xs">
                                                {s.renter_name || "Unknown"}
                                            </TableCell>
                                            <TableCell>
                                                {s.end_time ? (
                                                    <span className="text-xs bg-gray-100 text-gray-800 px-1 py-0.5 rounded">Finished</span>
                                                ) : (
                                                    <span className="text-xs bg-green-100 text-green-800 px-1 py-0.5 rounded animate-pulse">Active</span>
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                {!s.end_time ? (
                                                    <button 
                                                        onClick={(e) => handleRemoteStop(e, s.transaction_id)}
                                                        disabled={stoppingSessionId === s.transaction_id}
                                                        className="inline-flex items-center text-xs bg-red-100 hover:bg-red-200 text-red-700 px-2 py-1 rounded transition-colors disabled:opacity-50"
                                                    >
                                                        {stoppingSessionId === s.transaction_id ? (
                                                            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                                        ) : (
                                                            <PlugZap className="w-3 h-3 mr-1" />
                                                        )}
                                                        Stop
                                                    </button>
                                                ) : null}
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
                                    <LineChart data={chartDataMemo.chartData}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                        <XAxis
                                            dataKey="timestamp"
                                            tickFormatter={(str: string) => parseServerDate(str)?.toLocaleTimeString("de-CH") || ""}
                                            stroke="#888888"
                                            fontSize={12}
                                        />
                                        {chartDataMemo.uniqueUnits.map((unit, index) => (
                                            <YAxis
                                                key={unit}
                                                yAxisId={unit}
                                                orientation={index % 2 === 0 ? "left" : "right"}
                                                stroke="#888888"
                                                fontSize={12}
                                                domain={['auto', 'auto']}
                                                label={{ value: unit !== 'default' ? unit : '', angle: -90, position: 'insideLeft', offset: 10 }}
                                            />
                                        ))}
                                        <Tooltip
                                            labelFormatter={(str: string) => parseServerDate(str)?.toLocaleString("de-CH") || ""}
                                            content={({ active, payload, label }: { active?: boolean, payload?: any[], label?: string }) => {
                                                if (active && payload && payload.length) {
                                                    return (
                                                        <div className="bg-white border rounded p-2 shadow-sm text-sm dark:bg-gray-800 dark:border-gray-700">
                                                            <p className="font-semibold mb-1">{label ? parseServerDate(label)?.toLocaleString("de-CH") : ''}</p>
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
                                        <Legend onClick={handleLegendClick} wrapperStyle={{ cursor: 'pointer' }} />
                                        <Brush dataKey="timestamp" height={30} stroke="#8884d8" tickFormatter={(str: string) => parseServerDate(str)?.toLocaleTimeString("de-CH") || ""} />
                                        
                                        {Array.from(chartDataMemo.seriesUnitMap.entries()).map(([key, unit], index) => {
                                            const colors = ["#2563eb", "#dc2626", "#16a34a", "#ca8a04", "#9333ea", "#0891b2"];
                                            return (
                                                <Line
                                                    key={key}
                                                    type="monotone"
                                                    dataKey={key}
                                                    name={key}
                                                    yAxisId={unit}
                                                    hide={hiddenSeries[key]}
                                                    stroke={colors[index % colors.length]}
                                                    dot={false}
                                                    strokeWidth={2}
                                                    connectNulls={true}
                                                />
                                            );
                                        })}
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
                            <div className="flex items-center justify-between mr-8">
                                <DialogTitle>OCPP Logs</DialogTitle>
                                <input 
                                    type="date"
                                    className="border rounded px-2 py-1 text-sm dark:bg-gray-800 dark:border-gray-700 outline-none focus:ring-2 focus:ring-ring"
                                    value={selectedLogDate}
                                    onChange={(e) => setSelectedLogDate(e.target.value)}
                                />
                            </div>
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
                                                {parseServerDate(log.timestamp)?.toLocaleTimeString("de-CH")}
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
