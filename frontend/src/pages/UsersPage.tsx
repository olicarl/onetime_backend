import { useEffect, useState } from "react";
import axios from "axios";
import { Sidebar } from "@/components/layout/sidebar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/providers/auth-provider";
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
import { Loader2, Plus, Trash2, Key } from "lucide-react";

interface User {
    id: number;
    username: string;
    role: string;
    is_active: boolean;
    created_at: string;
}

export default function UsersPage() {
    const { user: currentUser } = useAuth();
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [open, setOpen] = useState(false);

    // Change Password State
    const [changePassOpen, setChangePassOpen] = useState(false);
    const [newPass, setNewPass] = useState("");

    // Form state
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState("admin");

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const res = await axios.get("/api/admin/users");
            setUsers(res.data);
        } catch (error) {
            console.error("Failed to fetch users", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async () => {
        try {
            await axios.post("/api/admin/users", {
                username,
                password,
                role,
                is_active: true
            });
            setOpen(false);
            setUsername("");
            setPassword("");
            fetchUsers();
        } catch (error) {
            console.error("Failed to create user", error);
            alert("Failed to create user");
        }
    };

    const handleDeleteUser = async (id: number) => {
        if (!confirm("Are you sure?")) return;
        try {
            await axios.delete(`/api/admin/users/${id}`);
            fetchUsers();
        } catch (error) {
            console.error("Failed to delete user", error);
        }
    };

    const handleChangePassword = async () => {
        if (!currentUser) return;
        try {
            await axios.put(`/api/admin/users/${currentUser.id}`, {
                password: newPass
            });
            setChangePassOpen(false);
            setNewPass("");
            alert("Password updated successfully");
        } catch (error) {
            console.error("Failed to update password", error);
            alert("Failed to update password");
        }
    };

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-8 bg-gray-50 dark:bg-gray-900">
                <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold tracking-tight">Users</h2>
                    <div className="flex gap-2">
                        <Dialog open={changePassOpen} onOpenChange={setChangePassOpen}>
                            <DialogTrigger asChild>
                                <Button variant="outline">
                                    <Key className="mr-2 h-4 w-4" /> Change My Password
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-[425px]">
                                <DialogHeader>
                                    <DialogTitle>Change Password</DialogTitle>
                                    <DialogDescription>
                                        Update your password.
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label htmlFor="newPass" className="text-right">
                                            New Password
                                        </Label>
                                        <Input
                                            id="newPass"
                                            type="password"
                                            value={newPass}
                                            onChange={(e) => setNewPass(e.target.value)}
                                            className="col-span-3"
                                        />
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button onClick={handleChangePassword}>Update Password</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>

                        <Dialog open={open} onOpenChange={setOpen}>
                            <DialogTrigger asChild>
                                <Button>
                                    <Plus className="mr-2 h-4 w-4" /> Add User
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-[425px]">
                                <DialogHeader>
                                    <DialogTitle>Add User</DialogTitle>
                                    <DialogDescription>
                                        Create a new user account.
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label htmlFor="username" className="text-right">
                                            Username
                                        </Label>
                                        <Input
                                            id="username"
                                            value={username}
                                            onChange={(e) => setUsername(e.target.value)}
                                            className="col-span-3"
                                        />
                                    </div>
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label htmlFor="password" className="text-right">
                                            Password
                                        </Label>
                                        <Input
                                            id="password"
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="col-span-3"
                                        />
                                    </div>
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label htmlFor="role" className="text-right">
                                            Role
                                        </Label>
                                        <Input
                                            id="role"
                                            value={role}
                                            onChange={(e) => setRole(e.target.value)}
                                            className="col-span-3"
                                        />
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button onClick={handleCreateUser}>Save changes</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    </div>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>All Users</CardTitle>
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
                                        <TableHead>ID</TableHead>
                                        <TableHead>Username</TableHead>
                                        <TableHead>Role</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Created At</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {users.map((user) => (
                                        <TableRow key={user.id}>
                                            <TableCell>{user.id}</TableCell>
                                            <TableCell className="font-medium">{user.username}</TableCell>
                                            <TableCell>{user.role}</TableCell>
                                            <TableCell>
                                                {user.is_active ? (
                                                    <span className="text-green-600 font-medium">Active</span>
                                                ) : (
                                                    <span className="text-red-500">Inactive</span>
                                                )}
                                            </TableCell>
                                            <TableCell>{new Date(user.created_at).toLocaleDateString()}</TableCell>
                                            <TableCell className="text-right">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="text-red-500 hover:text-red-700"
                                                    onClick={() => handleDeleteUser(user.id)}
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
