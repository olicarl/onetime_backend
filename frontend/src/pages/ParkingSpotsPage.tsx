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
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Plus, Trash2, Edit } from "lucide-react";
import { DeleteConfirmationDialog } from "@/components/ui/delete-confirmation-dialog";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

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
    contact_email: string;
}

interface Charger {
    id: string;
    vendor: string | null;
    model: string | null;
    is_online: boolean;
    parking_spot_label: string | null;
    parking_spot_id: number | null;
}

export default function ParkingSpotsPage() {
    const [spots, setSpots] = useState<ParkingSpot[]>([]);
    const [renters, setRenters] = useState<Renter[]>([]);
    const [chargers, setChargers] = useState<Charger[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<"spots" | "chargers">("spots");

    // Spot Dialog State
    const [spotDialogOpen, setSpotDialogOpen] = useState(false);
    const [editingSpot, setEditingSpot] = useState<ParkingSpot | null>(null);
    const [spotForm, setSpotForm] = useState({
        label: "",
        floor_level: "",
        renter_id: "",
        charging_station_id: ""
    });

    // Charger Dialog State (Edit only)
    const [chargerDialogOpen, setChargerDialogOpen] = useState(false);
    const [editingCharger, setEditingCharger] = useState<Charger | null>(null);
    const [chargerForm, setChargerForm] = useState({
        vendor: "",
        model: "",
        parking_spot_id: ""
    });

    // Delete Confirmation State
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [itemToDelete, setItemToDelete] = useState<{ type: 'spot' | 'charger', id: number | string, name?: string } | null>(null);

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

    // --- Spot Actions ---

    const openCreateSpot = () => {
        setEditingSpot(null);
        setSpotForm({ label: "", floor_level: "", renter_id: "", charging_station_id: "" });
        setSpotDialogOpen(true);
    };

    const openEditSpot = (spot: ParkingSpot) => {
        setEditingSpot(spot);
        setSpotForm({
            label: spot.label,
            floor_level: spot.floor_level || "",
            renter_id: spot.renter_id ? spot.renter_id.toString() : "",
            charging_station_id: spot.charging_station_id || ""
        });
        setSpotDialogOpen(true);
    };

    const handleSaveSpot = async () => {
        try {
            const payload = {
                label: spotForm.label,
                floor_level: spotForm.floor_level || null,
                renter_id: spotForm.renter_id ? parseInt(spotForm.renter_id) : null,
                charging_station_id: spotForm.charging_station_id || null
            };

            if (editingSpot) {
                await axios.put(`/api/admin/parking-spots/${editingSpot.id}`, payload);
            } else {
                await axios.post("/api/admin/parking-spots", payload);
            }
            setSpotDialogOpen(false);
            fetchData();
        } catch (error) {
            console.error("Failed to save parking spot", error);
            alert("Failed to save parking spot");
        }
    };

    const confirmDeleteSpot = (spot: ParkingSpot) => {
        setItemToDelete({ type: 'spot', id: spot.id, name: spot.label });
        setDeleteDialogOpen(true);
    };

    // --- Charger Actions ---

    const openEditCharger = (charger: Charger) => {
        setEditingCharger(charger);
        setChargerForm({
            vendor: charger.vendor || "",
            model: charger.model || "",
            parking_spot_id: charger.parking_spot_id ? charger.parking_spot_id.toString() : ""
        });
        setChargerDialogOpen(true);
    };

    const handleSaveCharger = async () => {
        if (!editingCharger) return;
        try {
            const payload = {
                vendor: chargerForm.vendor || null,
                model: chargerForm.model || null,
                parking_spot_id: chargerForm.parking_spot_id ? parseInt(chargerForm.parking_spot_id) : null
            };

            await axios.put(`/api/admin/chargers/${editingCharger.id}`, payload);
            setChargerDialogOpen(false);
            fetchData();
        } catch (error) {
            console.error("Failed to update charger", error);
            alert("Failed to update charger");
        }
    };

    const confirmDeleteCharger = (charger: Charger) => {
        setItemToDelete({ type: 'charger', id: charger.id, name: charger.id });
        setDeleteDialogOpen(true);
    };

    const handleConfirmDelete = async () => {
        if (!itemToDelete) return;

        try {
            if (itemToDelete.type === 'spot') {
                await axios.delete(`/api/admin/parking-spots/${itemToDelete.id}`);
            } else {
                await axios.delete(`/api/admin/chargers/${itemToDelete.id}`);
            }
            fetchData();
        } catch (error) {
            console.error("Failed to delete item", error);
            alert("Failed to delete item. It may have active dependencies.");
        } finally {
            setDeleteDialogOpen(false);
            setItemToDelete(null);
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
                    <h2 className="text-3xl font-bold tracking-tight">Parking Management</h2>
                    {activeTab === "spots" && (
                        <Button onClick={openCreateSpot}>
                            <Plus className="mr-2 h-4 w-4" /> Add Spot
                        </Button>
                    )}
                </div>

                {/* Custom Tabs */}
                <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex space-x-8">
                        <button
                            onClick={() => setActiveTab("spots")}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === "spots"
                                ? "border-primary text-primary"
                                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                }`}
                        >
                            Parking Spots
                        </button>
                        <button
                            onClick={() => setActiveTab("chargers")}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === "chargers"
                                ? "border-primary text-primary"
                                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                }`}
                        >
                            Charging Stations
                        </button>
                    </div>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>{activeTab === "spots" ? "All Parking Spots" : "Charging Stations"}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="flex justify-center p-8">
                                <Loader2 className="h-8 w-8 animate-spin" />
                            </div>
                        ) : activeTab === "spots" ? (
                            // --- SPOTS TABLE ---
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
                                                    onClick={() => openEditSpot(spot)}
                                                >
                                                    <Edit className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="text-red-500 hover:text-red-700"
                                                    onClick={() => confirmDeleteSpot(spot)}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        ) : (
                            // --- CHARGERS TABLE ---
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Charge Point ID</TableHead>
                                        <TableHead>Vendor/Model</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Linked Spot</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {chargers.map((charger) => (
                                        <TableRow key={charger.id}>
                                            <TableCell className="font-mono">{charger.id}</TableCell>
                                            <TableCell>
                                                <div className="flex flex-col">
                                                    <span className="font-medium">{charger.vendor || "Unknown"}</span>
                                                    <span className="text-xs text-muted-foreground">{charger.model || "-"}</span>
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <span className={`font-medium ${charger.is_online ? 'text-green-600' : 'text-gray-500'}`}>
                                                    {charger.is_online ? "Online" : "Offline"}
                                                </span>
                                            </TableCell>
                                            <TableCell>
                                                {charger.parking_spot_label ? (
                                                    <span className="font-medium">{charger.parking_spot_label}</span>
                                                ) : (
                                                    <span className="text-muted-foreground italic">Unlinked</span>
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => openEditCharger(charger)}
                                                >
                                                    <Edit className="h-4 w-4" />
                                                </Button>

                                                {charger.is_online ? (
                                                    <TooltipProvider>
                                                        <Tooltip>
                                                            <TooltipTrigger asChild>
                                                                <span tabIndex={0}> {/* Span needed for disabled button tooltip trigger */}
                                                                    <Button
                                                                        variant="ghost"
                                                                        size="icon"
                                                                        className="text-gray-400 cursor-not-allowed"
                                                                        disabled
                                                                    >
                                                                        <Trash2 className="h-4 w-4" />
                                                                    </Button>
                                                                </span>
                                                            </TooltipTrigger>
                                                            <TooltipContent>
                                                                <p>Cannot delete an online charger.<br />Please disconnect it first.</p>
                                                            </TooltipContent>
                                                        </Tooltip>
                                                    </TooltipProvider>
                                                ) : (
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="text-red-500 hover:text-red-700"
                                                        onClick={() => confirmDeleteCharger(charger)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                )}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>

                <DeleteConfirmationDialog
                    open={deleteDialogOpen}
                    onOpenChange={setDeleteDialogOpen}
                    onConfirm={handleConfirmDelete}
                    title={`Delete ${itemToDelete?.type === 'spot' ? 'Parking Spot' : 'Charging Station'}?`}
                    description={`Are you sure you want to delete this ${itemToDelete?.type === 'spot' ? 'parking spot' : 'charging station'}? This action cannot be undone.`}
                    itemDescription={itemToDelete?.name}
                />

                {/* Spot CREATE/EDIT Dialog */}
                <Dialog open={spotDialogOpen} onOpenChange={setSpotDialogOpen}>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>{editingSpot ? "Edit Parking Spot" : "Add Parking Spot"}</DialogTitle>
                            <DialogDescription>
                                {editingSpot ? "Update spot details and relations." : "Create a new parking spot."}
                            </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="label" className="text-right">Label</Label>
                                <Input
                                    id="label"
                                    value={spotForm.label}
                                    onChange={(e) => setSpotForm({ ...spotForm, label: e.target.value })}
                                    className="col-span-3"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="floor" className="text-right">Floor</Label>
                                <Input
                                    id="floor"
                                    value={spotForm.floor_level}
                                    onChange={(e) => setSpotForm({ ...spotForm, floor_level: e.target.value })}
                                    className="col-span-3"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="renter" className="text-right">Renter</Label>
                                <select
                                    id="renter"
                                    value={spotForm.renter_id}
                                    onChange={(e) => setSpotForm({ ...spotForm, renter_id: e.target.value })}
                                    className="col-span-3 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    <option value="">-- None --</option>
                                    {renters.map(r => (
                                        <option key={r.id} value={r.id}>{r.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="charger" className="text-right">Charger</Label>
                                <select
                                    id="charger"
                                    value={spotForm.charging_station_id}
                                    onChange={(e) => setSpotForm({ ...spotForm, charging_station_id: e.target.value })}
                                    className="col-span-3 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    <option value="">-- None --</option>
                                    {chargers.map(c => {
                                        // Show if unlinked OR if currently linked to THIS spot
                                        const isLinkedToOther = c.parking_spot_id && (!editingSpot || c.parking_spot_id !== editingSpot.id);
                                        // Complex logic: API get_chargers doesn't easily tell us WHICH spot is linked unless we check model.
                                        // Helper: c.parking_spot_id is valid.
                                        if (isLinkedToOther) return null; // Filter out taken chargers? Or show disabled?
                                        // Just show all for now, backend might error or handle overwrite.
                                        // Better: Filter out those linked to OTHER spots.

                                        // Let's rely on basic map, user can select.
                                        return <option key={c.id} value={c.id}>{c.id}</option>
                                    })}
                                    {/* Fallback to ensure current one is visible if valid? */}
                                    {/* Simple map for now. */}
                                </select>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleSaveSpot}>Save</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                {/* Charger EDIT Dialog */}
                <Dialog open={chargerDialogOpen} onOpenChange={setChargerDialogOpen}>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>Edit Charging Station</DialogTitle>
                            <DialogDescription>
                                Update information and link to a parking spot.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label className="text-right">ID</Label>
                                <span className="col-span-3 font-mono text-sm">{editingCharger?.id}</span>
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="cVendor" className="text-right">Vendor</Label>
                                <Input
                                    id="cVendor"
                                    value={chargerForm.vendor}
                                    onChange={(e) => setChargerForm({ ...chargerForm, vendor: e.target.value })}
                                    className="col-span-3"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="cModel" className="text-right">Model</Label>
                                <Input
                                    id="cModel"
                                    value={chargerForm.model}
                                    onChange={(e) => setChargerForm({ ...chargerForm, model: e.target.value })}
                                    className="col-span-3"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="cSpot" className="text-right">Parking Spot</Label>
                                <select
                                    id="cSpot"
                                    value={chargerForm.parking_spot_id}
                                    onChange={(e) => setChargerForm({ ...chargerForm, parking_spot_id: e.target.value })}
                                    className="col-span-3 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    <option value="">-- Unlinked --</option>
                                    {spots.map(s => (
                                        <option key={s.id} value={s.id}>{s.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleSaveCharger}>Save</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </main>
        </div>
    );
}
