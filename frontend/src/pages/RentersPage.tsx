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

interface Renter {
    id: number;
    name: string;
    contact_email: string;
    phone_number: string | null;
    is_active: boolean;
    created_at: string;
}

interface AuthorizationToken {
    token: string;
    renter_id: number | null;
    description: string | null;
    status: string;
    expiry_date: string | null;
    renter?: Renter;
}

export default function RentersPage() {
    const [renters, setRenters] = useState<Renter[]>([]);
    const [tokens, setTokens] = useState<AuthorizationToken[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<"renters" | "tokens">("renters");

    // Renter Dialog State
    const [renterDialogOpen, setRenterDialogOpen] = useState(false);
    const [editingRenter, setEditingRenter] = useState<Renter | null>(null);
    const [renterForm, setRenterForm] = useState({ name: "", email: "", phone: "" });

    // Token Dialog State
    const [tokenDialogOpen, setTokenDialogOpen] = useState(false);
    const [editingToken, setEditingToken] = useState<AuthorizationToken | null>(null);
    const [tokenForm, setTokenForm] = useState({
        token: "",
        renter_id: "" as string | number, // use string for select 'none'
        description: "",
        status: "Accepted"
    });

    // Delete Confirmation State
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [itemToDelete, setItemToDelete] = useState<{ type: 'renter' | 'token', id: number | string, name?: string } | null>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [rentersRes, tokensRes] = await Promise.all([
                axios.get("/api/admin/renters"),
                axios.get("/api/admin/auth-tokens")
            ]);
            setRenters(rentersRes.data);
            setTokens(tokensRes.data);
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setLoading(false);
        }
    };

    // --- Renter Actions ---

    const openCreateRenter = () => {
        setEditingRenter(null);
        setRenterForm({ name: "", email: "", phone: "" });
        setRenterDialogOpen(true);
    };

    const openEditRenter = (renter: Renter) => {
        setEditingRenter(renter);
        setRenterForm({
            name: renter.name,
            email: renter.contact_email,
            phone: renter.phone_number || ""
        });
        setRenterDialogOpen(true);
    };

    const handleSaveRenter = async () => {
        // Validation
        if (!renterForm.name.trim()) {
            alert("Name is required");
            return;
        }
        if (!renterForm.email.trim()) {
            alert("Email is required");
            return;
        }
        // Simple email regex
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(renterForm.email)) {
            alert("Please enter a valid email address");
            return;
        }

        try {
            const payload = {
                name: renterForm.name,
                contact_email: renterForm.email,
                phone_number: renterForm.phone || null,
                is_active: true
            };

            if (editingRenter) {
                await axios.put(`/api/admin/renters/${editingRenter.id}`, payload);
            } else {
                await axios.post("/api/admin/renters", payload);
            }
            setRenterDialogOpen(false);
            fetchData();
        } catch (error) {
            console.error("Failed to save renter", error);
            alert("Failed to save renter");
        }
    };


    const confirmDeleteRenter = (renter: Renter) => {
        setItemToDelete({ type: 'renter', id: renter.id, name: renter.name });
        setDeleteDialogOpen(true);
    };

    // --- Token Actions ---

    const openEditToken = (token: AuthorizationToken) => {
        setEditingToken(token);
        setTokenForm({
            token: token.token,
            renter_id: token.renter_id || "",
            description: token.description || "",
            status: token.status
        });
        setTokenDialogOpen(true);
    };

    // Logic for manually creating a token if needed, mainly specific for editing though

    const openCreateToken = () => {
        setEditingToken(null);
        setTokenForm({
            token: "",
            renter_id: "",
            description: "",
            status: "Accepted"
        });
        setTokenDialogOpen(true);
    };

    // Logic for manually creating or updating a token
    const handleSaveToken = async () => {
        try {
            const payload = {
                token: tokenForm.token,
                renter_id: tokenForm.renter_id === "" ? null : Number(tokenForm.renter_id),
                description: tokenForm.description,
                status: tokenForm.status
            };

            if (editingToken) {
                // Update existing
                // payload.token is ignored by backend for update usually, but we need it for URL
                await axios.put(`/api/admin/auth-tokens/${editingToken.token}`, {
                    renter_id: payload.renter_id,
                    description: payload.description,
                    status: payload.status
                });
            } else {
                // Create new
                await axios.post("/api/admin/auth-tokens", {
                    ...payload,
                    // Ensure token is set
                    token: tokenForm.token
                });
            }
            setTokenDialogOpen(false);
            fetchData();
        } catch (error) {
            console.error("Failed to save token", error);
            alert("Failed to save token");
        }
    };

    const confirmDeleteToken = (token: AuthorizationToken) => {
        setItemToDelete({ type: 'token', id: token.token, name: token.token });
        setDeleteDialogOpen(true);
    };

    const handleConfirmDelete = async () => {
        if (!itemToDelete) return;

        try {
            if (itemToDelete.type === 'renter') {
                await axios.delete(`/api/admin/renters/${itemToDelete.id}`);
            } else {
                await axios.delete(`/api/admin/auth-tokens/${itemToDelete.id}`);
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


    // --- Helpers ---

    const getLinkedTokens = (renterId: number) => {
        return tokens.filter(t => t.renter_id === renterId);
    };

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-8 bg-gray-50 dark:bg-gray-900">
                <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold tracking-tight">Renter Management</h2>
                    {activeTab === "renters" ? (
                        <Button onClick={openCreateRenter}>
                            <Plus className="mr-2 h-4 w-4" /> Add Renter
                        </Button>
                    ) : (
                        <Button onClick={openCreateToken}>
                            <Plus className="mr-2 h-4 w-4" /> Add Token
                        </Button>
                    )}
                </div>

                {/* Custom Tabs */}
                <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex space-x-8">
                        <button
                            onClick={() => setActiveTab("renters")}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === "renters"
                                ? "border-primary text-primary"
                                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                }`}
                        >
                            Renters
                        </button>
                        <button
                            onClick={() => setActiveTab("tokens")}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === "tokens"
                                ? "border-primary text-primary"
                                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                }`}
                        >
                            Authorization Tokens
                        </button>
                    </div>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>{activeTab === "renters" ? "All Renters" : "Authorization Tokens"}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="flex justify-center p-8">
                                <Loader2 className="h-8 w-8 animate-spin" />
                            </div>
                        ) : activeTab === "renters" ? (
                            // --- RENTERS TABLE ---
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Name</TableHead>
                                        <TableHead>Email</TableHead>
                                        <TableHead>Phone</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Linked Tokens</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {renters.map((renter) => {
                                        const linkedTokens = getLinkedTokens(renter.id);
                                        return (
                                            <TableRow key={renter.id}>
                                                <TableCell className="font-medium">{renter.name}</TableCell>
                                                <TableCell>{renter.contact_email}</TableCell>
                                                <TableCell>{renter.phone_number || "-"}</TableCell>
                                                <TableCell>
                                                    {renter.is_active ? (
                                                        <span className="text-green-600 font-medium">Active</span>
                                                    ) : (
                                                        <span className="text-red-500">Inactive</span>
                                                    )}
                                                </TableCell>
                                                <TableCell>
                                                    {linkedTokens.length > 0 ? (
                                                        <div className="flex flex-wrap gap-1">
                                                            {linkedTokens.map(t => (
                                                                <span key={t.token} className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">
                                                                    {t.token}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    ) : (
                                                        <span className="text-muted-foreground text-sm">None</span>
                                                    )}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => openEditRenter(renter)}
                                                    >
                                                        <Edit className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="text-red-500 hover:text-red-700"
                                                        onClick={() => confirmDeleteRenter(renter)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        ) : (
                            // --- TOKENS TABLE ---
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Token ID</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Description</TableHead>
                                        <TableHead>Linked Renter</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {tokens.map((token) => {
                                        const renter = renters.find(r => r.id === token.renter_id);
                                        return (
                                            <TableRow key={token.token}>
                                                <TableCell className="font-mono">{token.token}</TableCell>
                                                <TableCell>
                                                    <span className={`font-medium ${token.status === 'Accepted' ? 'text-green-600' :
                                                        token.status === 'Blocked' ? 'text-red-600' :
                                                            token.status === 'Unknown' ? 'text-orange-500' :
                                                                'text-gray-600'
                                                        }`}>
                                                        {token.status}
                                                    </span>
                                                </TableCell>
                                                <TableCell>{token.description || "-"}</TableCell>
                                                <TableCell>
                                                    {renter ? (
                                                        <span className="font-medium">{renter.name}</span>
                                                    ) : (
                                                        <span className="text-muted-foreground italic">Unlinked</span>
                                                    )}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => openEditToken(token)}
                                                    >
                                                        <Edit className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="text-red-500 hover:text-red-700"
                                                        onClick={() => confirmDeleteToken(token)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>

                <DeleteConfirmationDialog
                    open={deleteDialogOpen}
                    onOpenChange={setDeleteDialogOpen}
                    onConfirm={handleConfirmDelete}
                    title={`Delete ${itemToDelete?.type === 'renter' ? 'Renter' : 'Token'}?`}
                    description={`Are you sure you want to delete this ${itemToDelete?.type}? This action cannot be undone.`}
                    itemDescription={itemToDelete?.name}
                />

                {/* Renter CREATE/EDIT Dialog */}
                <Dialog open={renterDialogOpen} onOpenChange={setRenterDialogOpen}>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>{editingRenter ? "Edit Renter" : "Add Renter"}</DialogTitle>
                            <DialogDescription>
                                {editingRenter ? "Update renter details." : "Add a new renter to the system."}
                            </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="name" className="text-right">
                                    Name <span className="text-red-500">*</span>
                                </Label>
                                <Input
                                    id="name"
                                    value={renterForm.name}
                                    onChange={(e) => setRenterForm({ ...renterForm, name: e.target.value })}
                                    className="col-span-3"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="email" className="text-right">
                                    Email <span className="text-red-500">*</span>
                                </Label>
                                <Input
                                    id="email"
                                    type="email"
                                    required
                                    value={renterForm.email}
                                    onChange={(e) => setRenterForm({ ...renterForm, email: e.target.value })}
                                    className="col-span-3"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="phone" className="text-right">Phone</Label>
                                <Input
                                    id="phone"
                                    value={renterForm.phone}
                                    onChange={(e) => setRenterForm({ ...renterForm, phone: e.target.value })}
                                    className="col-span-3"
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button
                                onClick={handleSaveRenter}
                                disabled={!renterForm.name.trim() || !renterForm.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(renterForm.email)}
                            >
                                Save
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                {/* Token EDIT Dialog */}
                <Dialog open={tokenDialogOpen} onOpenChange={setTokenDialogOpen}>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>{editingToken ? "Edit Token" : "Add Token"}</DialogTitle>
                            <DialogDescription>
                                {editingToken ? "Update token status and linked renter." : "Manually add a new authorization token."}
                            </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label className="text-right">Token ID</Label>
                                {editingToken ? (
                                    <span className="col-span-3 font-mono text-sm">{editingToken.token}</span>
                                ) : (
                                    <Input
                                        value={tokenForm.token}
                                        onChange={(e) => setTokenForm({ ...tokenForm, token: e.target.value })}
                                        placeholder="UID (e.g. DEADBEEF)"
                                        className="col-span-3 font-mono"
                                    />
                                )}
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="tokenStatus" className="text-right">Status</Label>
                                <select
                                    id="tokenStatus"
                                    className="col-span-3 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                    value={tokenForm.status}
                                    onChange={(e) => setTokenForm({ ...tokenForm, status: e.target.value })}
                                >
                                    <option value="Accepted">Accepted</option>
                                    <option value="Blocked">Blocked</option>
                                    <option value="Expired">Expired</option>
                                    <option value="Invalid">Invalid</option>
                                    <option value="Unknown">Unknown</option>
                                </select>
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="tokenRenter" className="text-right">Renter</Label>
                                <select
                                    id="tokenRenter"
                                    className="col-span-3 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                    value={tokenForm.renter_id}
                                    onChange={(e) => setTokenForm({ ...tokenForm, renter_id: e.target.value })}
                                >
                                    <option value="">-- Unlinked --</option>
                                    {renters.map(r => (
                                        <option key={r.id} value={r.id}>{r.name} ({r.contact_email})</option>
                                    ))}
                                </select>
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="tokenDesc" className="text-right">Description</Label>
                                <Input
                                    id="tokenDesc"
                                    value={tokenForm.description}
                                    onChange={(e) => setTokenForm({ ...tokenForm, description: e.target.value })}
                                    className="col-span-3"
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleSaveToken}>Save</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </main>
        </div>
    );
}

