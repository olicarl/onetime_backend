import { useState, useEffect } from "react";
import axios from "axios";
import { Sidebar } from "@/components/layout/sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Download, FileText, CheckCircle2, PlusCircle, History, Trash2, Eye } from "lucide-react";
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

interface Renter {
    id: number;
    name: string;
    contact_email: string;
    prepaid_balance_kwh: number;
}

// Removed BillingSettings interface

interface Invoice {
    id: number;
    renter_id: number;
    renter_name: string;
    period_start: string;
    period_end: string;
    amount_due: number;
    is_paid: boolean;
    created_at: string;
}

interface SessionInvoice {
    id: number;
    transaction_id: number;
    start_time: string;
    end_time: string | null;
    total_energy_kwh: number | null;
}

interface InvoiceDetails extends Invoice {
    sessions: SessionInvoice[];
}

export default function BillingPage() {
    const [loading, setLoading] = useState(true);
    
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [renters, setRenters] = useState<Renter[]>([]);
    const [billingMode, setBillingMode] = useState<string>("Postpaid");

    // Manual invoice modal states
    const [generateModalOpen, setGenerateModalOpen] = useState(false);
    const [generateForm, setGenerateForm] = useState({
        renter_id: "",
        end_date: new Date().toISOString().split('T')[0]
    });
    const [generating, setGenerating] = useState(false);

    // Prepaid Modals
    const [topUpModalOpen, setTopUpModalOpen] = useState(false);
    const [selectedRenterForTopUp, setSelectedRenterForTopUp] = useState<Renter | null>(null);
    const [topUpAmount, setTopUpAmount] = useState<number>(0);
    const [toppingUp, setToppingUp] = useState(false);

    const [historyModalOpen, setHistoryModalOpen] = useState(false);
    const [selectedRenterForHistory, setSelectedRenterForHistory] = useState<Renter | null>(null);
    const [prepaidHistory, setPrepaidHistory] = useState<any[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);

    const [viewInvoiceModalOpen, setViewInvoiceModalOpen] = useState(false);
    const [selectedInvoice, setSelectedInvoice] = useState<InvoiceDetails | null>(null);
    const [viewLoading, setViewLoading] = useState(false);
    
    // Deletion confirmation state
    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [invoiceToDelete, setInvoiceToDelete] = useState<number | null>(null);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [invoicesRes, rentersRes, settingsRes] = await Promise.all([
                axios.get("/api/billing/invoices"),
                axios.get("/api/admin/renters"),
                axios.get("/api/billing/settings")
            ]);
            setInvoices(invoicesRes.data);
            setRenters(rentersRes.data);
            setBillingMode(settingsRes.data.billing_mode || "Postpaid");
        } catch (error) {
            console.error("Failed to fetch billing data", error);
        } finally {
            setLoading(false);
        }
    };

// Handle save settings moved to SettingsPage

    const handleMarkPaid = async (invoiceId: number) => {
        try {
            await axios.post(`/api/billing/invoices/${invoiceId}/mark-paid`);
            fetchData();
        } catch (error) {
            console.error("Failed to mark invoice as paid", error);
            alert("Failed to update invoice status");
        }
    };

    const handlePreviewPDF = (invoiceId: number) => {
        window.open(`/api/billing/invoices/${invoiceId}/pdf`, '_blank');
    };

    const handleViewInvoice = async (invoice: Invoice) => {
        setViewInvoiceModalOpen(true);
        setViewLoading(true);
        try {
            const res = await axios.get(`/api/billing/invoices/${invoice.id}/details`);
            setSelectedInvoice(res.data);
        } catch (error) {
            console.error("Failed to load invoice details", error);
            alert("Failed to load invoice details");
            setViewInvoiceModalOpen(false);
        } finally {
            setViewLoading(false);
        }
    };

    const confirmDeleteInvoice = (invoiceId: number) => {
        setInvoiceToDelete(invoiceId);
        setDeleteModalOpen(true);
    };

    const handleDeleteInvoice = async () => {
        if (!invoiceToDelete) return;
        setDeleting(true);
        try {
            await axios.delete(`/api/billing/invoices/${invoiceToDelete}`);
            setDeleteModalOpen(false);
            setInvoiceToDelete(null);
            fetchData();
        } catch (error) {
            console.error("Failed to delete invoice", error);
            alert("Failed to delete invoice");
        } finally {
            setDeleting(false);
        }
    };

    const handleGenerateManualInvoice = async () => {
        if (!generateForm.renter_id) {
            alert("Please select a renter.");
            return;
        }
        setGenerating(true);
        try {
            // Include end of day for the selected date
            const fullEndDate = `${generateForm.end_date}T23:59:59Z`;
            
            const res = await axios.post("/api/billing/invoices/generate", {
                renter_id: Number(generateForm.renter_id),
                end_date: fullEndDate
            });
            
            if (res.data.invoice_id) {
                alert(`Success: Invoice ${res.data.invoice_id} generated.`);
            } else {
                alert(res.data.message); // e.g. "No unbilled sessions found"
            }
            
            setGenerateModalOpen(false);
            fetchData();
        } catch (error: any) {
            console.error("Failed to generate invoice", error);
            alert(error.response?.data?.detail || "Failed to generate invoice");
        } finally {
            setGenerating(false);
        }
    };

    const handleTopUp = async () => {
        if (!selectedRenterForTopUp || topUpAmount <= 0) {
            alert("Please enter a valid amount.");
            return;
        }
        setToppingUp(true);
        try {
            await axios.post(`/api/billing/renters/${selectedRenterForTopUp.id}/topup`, {
                amount_kwh: topUpAmount
            });
            alert("Top-up successful!");
            setTopUpModalOpen(false);
            fetchData(); // Refresh balances
        } catch (error: any) {
            console.error("Top up failed", error);
            alert(error.response?.data?.detail || "Top up failed");
        } finally {
            setToppingUp(false);
        }
    };

    const openHistory = async (renter: Renter) => {
        setSelectedRenterForHistory(renter);
        setHistoryModalOpen(true);
        setHistoryLoading(true);
        try {
            const res = await axios.get(`/api/billing/renters/${renter.id}/prepaid-details`);
            setPrepaidHistory(res.data.history || []);
        } catch (error) {
            console.error("Failed to load history", error);
            setPrepaidHistory([]);
        } finally {
            setHistoryLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-8 bg-gray-50 dark:bg-gray-900">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Billing Management</h2>
                        <span className="inline-block mt-2 px-2 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-800">
                            Mode: {billingMode}
                        </span>
                    </div>
                    {billingMode === "Postpaid" && (
                        <Button onClick={() => setGenerateModalOpen(true)}>
                            <FileText className="mr-2 h-4 w-4" /> Generate Invoice
                        </Button>
                    )}
                </div>

                {loading ? (
                    <div className="flex justify-center p-8">
                        <Loader2 className="h-8 w-8 animate-spin" />
                    </div>
                ) : billingMode === "Postpaid" ? (
                    <Card>
                        <CardHeader>
                            <CardTitle>Generated Invoices</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Invoice ID</TableHead>
                                        <TableHead>Renter</TableHead>
                                        <TableHead>Period</TableHead>
                                        <TableHead>Amount (CHF)</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {invoices.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={6} className="text-center text-muted-foreground py-4">
                                                No invoices generated yet.
                                            </TableCell>
                                        </TableRow>
                                    )}
                                    {invoices.map((inv) => (
                                        <TableRow key={inv.id}>
                                            <TableCell className="font-medium">#{inv.id}</TableCell>
                                            <TableCell>{inv.renter_name}</TableCell>
                                            <TableCell>
                                                {new Date(inv.period_start).toLocaleDateString("de-CH")} - {new Date(inv.period_end).toLocaleDateString("de-CH")}
                                            </TableCell>
                                            <TableCell>{inv.amount_due.toFixed(2)}</TableCell>
                                            <TableCell>
                                                {inv.is_paid ? (
                                                    <span className="inline-flex items-center text-green-600 bg-green-50 px-2 py-1 rounded-full text-xs font-medium">
                                                        <CheckCircle2 className="w-3 h-3 mr-1" /> Paid
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center text-amber-600 bg-amber-50 px-2 py-1 rounded-full text-xs font-medium">
                                                        Unpaid
                                                    </span>
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right space-x-2">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="text-xs"
                                                    onClick={() => handleMarkPaid(inv.id)}
                                                >
                                                    Mark {inv.is_paid ? 'Unpaid' : 'Paid'}
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    title="View Details"
                                                    onClick={() => handleViewInvoice(inv)}
                                                >
                                                    <Eye className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    title="Preview/Download PDF"
                                                    onClick={() => handlePreviewPDF(inv.id)}
                                                >
                                                    <Download className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    title="Delete Invoice"
                                                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                                    onClick={() => confirmDeleteInvoice(inv.id)}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                ) : (
                    <Card>
                        <CardHeader>
                            <CardTitle>Renter Prepaid Balances</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Renter Name</TableHead>
                                        <TableHead>Email</TableHead>
                                        <TableHead>Prepaid Balance (kWh)</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {renters.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center text-muted-foreground py-4">
                                                No renters found.
                                            </TableCell>
                                        </TableRow>
                                    )}
                                    {renters.map(renter => (
                                        <TableRow key={renter.id}>
                                            <TableCell className="font-medium">{renter.name}</TableCell>
                                            <TableCell>{renter.contact_email}</TableCell>
                                            <TableCell>
                                                <span className={`font-mono text-sm ${renter.prepaid_balance_kwh > 0 ? "text-green-600 font-bold" : "text-red-500"}`}>
                                                    {renter.prepaid_balance_kwh.toFixed(2)} kWh
                                                </span>
                                            </TableCell>
                                            <TableCell className="text-right space-x-2">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="text-xs"
                                                    onClick={() => {
                                                        setSelectedRenterForTopUp(renter);
                                                        setTopUpAmount(0);
                                                        setTopUpModalOpen(true);
                                                    }}
                                                >
                                                    <PlusCircle className="mr-1 w-3 h-3" /> Top Up
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => openHistory(renter)}
                                                >
                                                    <History className="w-4 h-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                )}
                
                {/* Generate Manual Invoice Dialog */}
                <Dialog open={generateModalOpen} onOpenChange={setGenerateModalOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Generate Manual Invoice</DialogTitle>
                            <DialogDescription>
                                Bill unbilled sessions up to a specific date for a renter.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid gap-2">
                                <Label htmlFor="renterSelect">Renter</Label>
                                <select
                                    id="renterSelect"
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    value={generateForm.renter_id}
                                    onChange={(e) => setGenerateForm({ ...generateForm, renter_id: e.target.value })}
                                >
                                    <option value="">-- Select Renter --</option>
                                    {renters.map(r => (
                                        <option key={r.id} value={r.id}>{r.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="endDate" className="mt-2">Billing Period End Date</Label>
                                <Input
                                    id="endDate"
                                    type="date"
                                    value={generateForm.end_date}
                                    onChange={(e) => setGenerateForm({ ...generateForm, end_date: e.target.value })}
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleGenerateManualInvoice} disabled={generating}>
                                {generating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                Generate Invoice
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                {/* Top Up Modal */}
                <Dialog open={topUpModalOpen} onOpenChange={setTopUpModalOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Top Up Balance</DialogTitle>
                            <DialogDescription>
                                Add prepaid energy (kWh) to {selectedRenterForTopUp?.name}'s account.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid gap-2">
                                <Label htmlFor="amount">Amount (kWh)</Label>
                                <Input
                                    id="amount"
                                    type="number"
                                    step="1"
                                    min="1"
                                    value={topUpAmount}
                                    onChange={(e) => setTopUpAmount(parseFloat(e.target.value))}
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleTopUp} disabled={toppingUp}>
                                {toppingUp ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                Add Funds
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                {/* History Modal */}
                <Dialog open={historyModalOpen} onOpenChange={setHistoryModalOpen}>
                    <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
                        <DialogHeader>
                            <DialogTitle>Prepaid History - {selectedRenterForHistory?.name}</DialogTitle>
                        </DialogHeader>
                        <div className="flex-1 overflow-auto mt-4">
                            {historyLoading ? (
                                <div className="flex justify-center py-8">
                                    <Loader2 className="w-6 h-6 animate-spin" />
                                </div>
                            ) : (
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Date</TableHead>
                                            <TableHead>Type</TableHead>
                                            <TableHead>Amount (kWh)</TableHead>
                                            <TableHead>Session ID</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {prepaidHistory.length === 0 && (
                                            <TableRow>
                                                <TableCell colSpan={4} className="text-center text-muted-foreground py-4">
                                                    No prepaid history found.
                                                </TableCell>
                                            </TableRow>
                                        )}
                                        {prepaidHistory.map((txn, i) => (
                                            <TableRow key={i}>
                                                <TableCell className="text-sm">{new Date(txn.timestamp).toLocaleString("de-CH")}</TableCell>
                                                <TableCell>
                                                    <span className={`px-2 py-1 text-xs font-semibold rounded ${txn.type === 'TopUp' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}`}>
                                                        {txn.type}
                                                    </span>
                                                </TableCell>
                                                <TableCell className="font-mono text-sm font-bold">
                                                    {txn.type === 'TopUp' ? '+' : '-'}{txn.amount_kwh.toFixed(3)}
                                                </TableCell>
                                                <TableCell className="font-mono text-xs text-muted-foreground">
                                                    {txn.transaction_id || "-"}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            )}
                        </div>
                    </DialogContent>
                </Dialog>

                {/* View Invoice Modal */}
                <Dialog open={viewInvoiceModalOpen} onOpenChange={setViewInvoiceModalOpen}>
                    <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
                        <DialogHeader>
                            <DialogTitle>Invoice Details</DialogTitle>
                        </DialogHeader>
                        <div className="flex-1 overflow-auto mt-4">
                            {viewLoading ? (
                                <div className="flex justify-center py-8">
                                    <Loader2 className="w-6 h-6 animate-spin" />
                                </div>
                            ) : selectedInvoice ? (
                                <div className="space-y-6">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                            <span className="font-semibold text-muted-foreground block">Invoice #</span>
                                            <div>{selectedInvoice.id}</div>
                                        </div>
                                        <div>
                                            <span className="font-semibold text-muted-foreground block">Renter</span>
                                            <div>{selectedInvoice.renter_name}</div>
                                        </div>
                                        <div>
                                            <span className="font-semibold text-muted-foreground block">Period</span>
                                            <div>
                                                {new Date(selectedInvoice.period_start).toLocaleDateString("de-CH")} - {new Date(selectedInvoice.period_end).toLocaleDateString("de-CH")}
                                            </div>
                                        </div>
                                        <div>
                                            <span className="font-semibold text-muted-foreground block">Status</span>
                                            <div>
                                                {selectedInvoice.is_paid ? (
                                                    <span className="inline-flex items-center text-green-600 font-medium">
                                                        <CheckCircle2 className="w-3 h-3 mr-1" /> Paid
                                                    </span>
                                                ) : "Unpaid"}
                                            </div>
                                        </div>
                                    </div>

                                    <div>
                                        <h4 className="font-semibold mb-3">Charging Sessions</h4>
                                        <div className="border rounded-md overflow-hidden">
                                            <Table>
                                                <TableHeader className="bg-gray-50 dark:bg-gray-800">
                                                    <TableRow>
                                                        <TableHead>Start Time</TableHead>
                                                        <TableHead>End Time</TableHead>
                                                        <TableHead className="text-right">Energy (kWh)</TableHead>
                                                    </TableRow>
                                                </TableHeader>
                                                <TableBody>
                                                    {selectedInvoice.sessions.length === 0 ? (
                                                        <TableRow>
                                                            <TableCell colSpan={3} className="text-center text-muted-foreground py-4">No sessions found.</TableCell>
                                                        </TableRow>
                                                    ) : (
                                                        selectedInvoice.sessions.map((s, i) => (
                                                            <TableRow key={i}>
                                                                <TableCell>{new Date(s.start_time).toLocaleString("de-CH")}</TableCell>
                                                                <TableCell>{s.end_time ? new Date(s.end_time).toLocaleString("de-CH") : "N/A"}</TableCell>
                                                                <TableCell className="text-right">
                                                                    {s.total_energy_kwh ? s.total_energy_kwh.toFixed(3) : "0.000"}
                                                                </TableCell>
                                                            </TableRow>
                                                        ))
                                                    )}
                                                </TableBody>
                                            </Table>
                                        </div>
                                    </div>
                                    
                                    <div className="flex justify-end pt-4 border-t">
                                        <div className="text-right">
                                            <span className="text-muted-foreground mr-4">Total Amount Due</span>
                                            <span className="text-xl font-bold">{selectedInvoice.amount_due.toFixed(2)} CHF</span>
                                        </div>
                                    </div>
                                </div>
                            ) : null}
                        </div>
                    </DialogContent>
                </Dialog>

                {/* Delete Confirmation Modal */}
                <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Delete Invoice</DialogTitle>
                            <DialogDescription>
                                Are you sure you want to delete this invoice? The associated charging sessions will be marked as unbilled, and the PDF will be deleted. This action cannot be undone.
                            </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setDeleteModalOpen(false)} disabled={deleting}>Cancel</Button>
                            <Button variant="destructive" onClick={handleDeleteInvoice} disabled={deleting}>
                                {deleting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                Delete
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </main>
        </div>
    );
}
