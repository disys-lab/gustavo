"use client";
import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/context/AuthContext";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

function LoginForm() {
  const [userId, setUserId] = useState("");
  const [userToken, setUserToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const result = await login(userId, userToken);
    setLoading(false);
    if (result.error) {
      setError(result.message ?? "Login failed");
    } else {
      const redirect = searchParams.get("redirect") ?? "/dashboard";
      router.push(redirect);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-xl border bg-white p-8 shadow-sm">
        <h1 className="mb-1 text-center text-xl font-bold text-gray-900">Sign in to Gustavo</h1>
        <p className="mb-6 text-center text-sm text-gray-500">Authenticate using your User ID and Token</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="userId">User ID</Label>
            <Input
              id="userId"
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              required
              autoComplete="username"
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="userToken">User Token</Label>
            <Input
              id="userToken"
              type="password"
              value={userToken}
              onChange={(e) => setUserToken(e.target.value)}
              required
              autoComplete="current-password"
              className="mt-1"
            />
          </div>
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Authenticating…" : "Login"}
          </Button>
        </form>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
