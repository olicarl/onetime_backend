import { useState, useEffect } from "react";
import axios from "axios";
import { Sidebar } from "@/components/layout/sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Download, FileText, CheckCircle2 } from "lucide-react";
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
}

interface BillingSettings {
    company_name: string;
    iban: string;
    address: string;
    periodicity: string;
    price_per_kwh: number;
}

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

export default function BillingPage() {
    const [activeTab, setActiveTab] = useState<"settings" | "invoices">("settings");
    const [loading, setLoading] = useState(true);

    const [settings, setSettings] = useState<BillingSettings>({
        company_name: "",
        iban: "",
        address: "",
        periodicity: "Monthly",
        price_per_kwh: 0
    });
    
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [renters, setRenters] = useState<Renter[]>([]);

    // Manual invoice modal states
    const [generateModalOpen, setGenerateModalOpen] = useState(false);
    const [generateForm, setGenerateForm] = useState({
        renter_id: "",
        end_date: new Date().toISOString().split('T')[0]
    });
    const [generating, setGenerating] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [settingsRes, invoicesRes, rentersRes] = await Promise.all([
                axios.get("/api/billing/settings"),
                axios.get("/api/billing/invoices"),
                axios.get("/api/admin/renters")
            ]);
            setSettings(settingsRes.data);
            setInvoices(invoicesRes.data);
            setRenters(rentersRes.data);
        } catch (error) {
            console.error("Failed to fetch billing data", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveSettings = async () => {
        try {
            await axios.put("/api/billing/settings", {
               ...settings,
               price_per_kwh: Number(settings.price_per_kwh)
            });
            alert("Settings saved successfully!");
            fetchData();
        } catch (error) {
            console.error("Failed to save settings", error);
            alert("Failed to save settings");
        }
    };

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

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-8 bg-gray-50 dark:bg-gray-900">
                <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold tracking-tight">Billing Management</h2>
                    {activeTab === "invoices" && (
                        <Button onClick={() => setGenerateModalOpen(true)}>
                            <FileText className="mr-2 h-4 w-4" /> Generate Invoice
                        </Button>
                    )}
                </div>

                <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex space-x-8">
                        <button
                            onClick={() => setActiveTab("settings")}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === "settings"
                                ? "border-primary text-primary"
                                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                }`}
                        >
                            Settings
                        </button>
                        <button
                            onClick={() => setActiveTab("invoices")}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === "invoices"
                                ? "border-primary text-primary"
                                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                }`}
                        >
                            Invoices
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center p-8">
                        <Loader2 className="h-8 w-8 animate-spin" />
                    </div>
                ) : activeTab === "settings" ? (
                    <Card className="max-w-2xl">
                        <CardHeader>
                            <CardTitle>Global Billing Configuration</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="grid gap-2">
                                <Label htmlFor="companyName">Company / Owner Name</Label>
                                <Input 
                                    id="companyName" 
                                    value={settings.company_name} 
                                    onChange={e => setSettings({...settings, company_name: e.target.value})}
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="iban">IBAN for QR Bill</Label>
                                <Input 
                                    id="iban" 
                                    value={settings.iban} 
                                    onChange={e => setSettings({...settings, iban: e.target.value})}
                                    placeholder="CHXX XXXX XXXX XXXX XXXX X"
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="address">Address (Include City/Zip, separated by comma)</Label>
                                <Input 
                                    id="address" 
                                    value={settings.address} 
                                    onChange={e => setSettings({...settings, address: e.target.value})}
                                    placeholder="Street 1, 1000 City"
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="periodicity">Billing Periodicity</Label>
                                <select
                                    id="periodicity"
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    value={settings.periodicity}
                                    onChange={(e) => setSettings({ ...settings, periodicity: e.target.value })}
                                >
                                    <option value="Monthly">Monthly</option>
                                    <option value="Quarterly">Quarterly</option>
                                    <option value="HalfYearly">Half Yearly</option>
                                    <option value="Yearly">Yearly</option>
                                </select>
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="price">Price per kWh (CHF)</Label>
                                <Input 
                                    id="price" 
                                    type="number"
                                    step="0.01"
                                    value={settings.price_per_kwh} 
                                    onChange={e => setSettings({...settings, price_per_kwh: parseFloat(e.target.value)})}
                                />
                            </div>
                            
                            <Button onClick={handleSaveSettings}>Save Configuration</Button>
                        </CardContent>
                    </Card>
                ) : (
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
                                                {new Date(inv.period_start).toLocaleDateString()} - {new Date(inv.period_end).toLocaleDateString()}
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
                                                    title="Preview/Download PDF"
                                                    onClick={() => handlePreviewPDF(inv.id)}
                                                >
                                                    <Download className="h-4 w-4" />
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
            </main>
        </div>
    );
}
