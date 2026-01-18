import { useEffect, useState } from "react";
import axios from "axios";
import { Sidebar } from "@/components/layout/sidebar";
import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Plus, Trash2 } from "lucide-react";

interface ParkingSpot {
    id: number;
    label: string;
    floor_level: string | null;
    renter_id: number | null;
    charging_station_id: string | null;
}

interface Renter {
    id: number;
    name: string;
}

interface Charger {
    id: string;
}

export default function ParkingSpotsPage() {
    const [spots, setSpots] = useState<ParkingSpot[]>([]);
    const [renters, setRenters] = useState<Renter[]>([]);
    const [chargers, setChargers] = useState<Charger[]>([]);
    const [loading, setLoading] = useState(true);
    const [open, setOpen] = useState(false);

    // Form state
    const [label, setLabel] = useState("");
    const [floor, setFloor] = useState("");
    const [selectedRenter, setSelectedRenter] = useState<string>("");
    const [selectedCharger, setSelectedCharger] = useState<string>("");

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [spotsRes, rentersRes, chargersRes] = await Promise.all([
                axios.get("/api/admin/parking-spots"),
                axios.get("/api/admin/renters"),
                axios.get("/api/admin/chargers"),
            ]);
            setSpots(spotsRes.data);
            setRenters(rentersRes.data);
            setChargers(chargersRes.data);
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateSpot = async () => {
        try {
            await axios.post("/api/admin/parking-spots", {
                label,
                floor_level: floor || null,
                renter_id: selectedRenter ? parseInt(selectedRenter) : null,
                charging_station_id: selectedCharger || null,
            });
            setOpen(false);
            setLabel("");
            setFloor("");
            setSelectedRenter("");
            setSelectedCharger("");
            // Refresh only spots
            const res = await axios.get("/api/admin/parking-spots");
            setSpots(res.data);
        } catch (error) {
            console.error("Failed to create parking spot", error);
            alert("Failed to create parking spot");
        }
    };

    const handleDeleteSpot = async (id: number) => {
        if (!confirm("Are you sure?")) return;
        try {
            await axios.delete(`/api/admin/parking-spots/${id}`);
            const res = await axios.get("/api/admin/parking-spots");
            setSpots(res.data);
        } catch (error) {
            console.error("Failed to delete parking spot", error);
        }
    };

    const getRenterName = (id: number | null) => {
        if (!id) return "-";
        return renters.find(r => r.id === id)?.name || id;
    };

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-8 bg-gray-50 dark:bg-gray-900">
                <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold tracking-tight">Parking Spots</h2>
                    <Dialog open={open} onOpenChange={setOpen}>
                        <DialogTrigger asChild>
                            <Button>
                                <Plus className="mr-2 h-4 w-4" /> Add Spot
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-[425px]">
                            <DialogHeader>
                                <DialogTitle>Add Parking Spot</DialogTitle>
                                <DialogDescription>
                                    Create a new parking spot and link it to a renter or charger.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="label" className="text-right">
                                        Label
                                    </Label>
                                    <Input
                                        id="label"
                                        value={label}
                                        onChange={(e) => setLabel(e.target.value)}
                                        className="col-span-3"
                                    />
                                </div>
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="floor" className="text-right">
                                        Floor
                                    </Label>
                                    <Input
                                        id="floor"
                                        value={floor}
                                        onChange={(e) => setFloor(e.target.value)}
                                        className="col-span-3"
                                    />
                                </div>
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="renter" className="text-right">
                                        Renter
                                    </Label>
                                    <select
                                        id="renter"
                                        value={selectedRenter}
                                        onChange={(e) => setSelectedRenter(e.target.value)}
                                        className="col-span-3 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                    >
                                        <option value="">None</option>
                                        {renters.map(r => (
                                            <option key={r.id} value={r.id}>{r.name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="charger" className="text-right">
                                        Charger
                                    </Label>
                                    <select
                                        id="charger"
                                        value={selectedCharger}
                                        onChange={(e) => setSelectedCharger(e.target.value)}
                                        className="col-span-3 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                    >
                                        <option value="">None</option>
                                        {chargers.map(c => (
                                            <option key={c.id} value={c.id}>{c.id}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <DialogFooter>
                                <Button onClick={handleCreateSpot}>Save changes</Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>All Parking Spots</CardTitle>
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
                                        <TableHead>Label</TableHead>
                                        <TableHead>Floor</TableHead>
                                        <TableHead>Renter</TableHead>
                                        <TableHead>Charger</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {spots.map((spot) => (
                                        <TableRow key={spot.id}>
                                            <TableCell className="font-medium">{spot.label}</TableCell>
                                            <TableCell>{spot.floor_level || "-"}</TableCell>
                                            <TableCell>{getRenterName(spot.renter_id)}</TableCell>
                                            <TableCell className="font-mono">{spot.charging_station_id || "-"}</TableCell>
                                            <TableCell className="text-right">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="text-red-500 hover:text-red-700"
                                                    onClick={() => handleDeleteSpot(spot.id)}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
