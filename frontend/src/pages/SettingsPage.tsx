import { useState, useEffect } from "react";
import axios from "axios";
import { Sidebar } from "@/components/layout/sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

interface BillingSettings {
    company_name: string;
    iban: string;
    address: string;
    periodicity: string;
    price_per_kwh: number;
}

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<"billing">("billing");
    const [loading, setLoading] = useState(true);

    const [settings, setSettings] = useState<BillingSettings>({
        company_name: "",
        iban: "",
        address: "",
        periodicity: "Monthly",
        price_per_kwh: 0
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await axios.get("/api/billing/settings");
            setSettings(res.data);
        } catch (error) {
            console.error("Failed to fetch settings data", error);
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

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-8 bg-gray-50 dark:bg-gray-900">
                <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
                </div>

                <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex space-x-8">
                        <button
                            onClick={() => setActiveTab("billing")}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === "billing"
                                ? "border-primary text-primary"
                                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                }`}
                        >
                            Billing settings for debt based billing
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center p-8">
                        <Loader2 className="h-8 w-8 animate-spin" />
                    </div>
                ) : activeTab === "billing" ? (
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
                ) : null}
            </main>
        </div>
    );
}
