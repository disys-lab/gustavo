"use client";
import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { useAuth } from "@/lib/context/AuthContext";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

function LoginForm() {
  const [credential, setCredential] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFirebase, setShowFirebase] = useState(false);
  const [userId, setUserId] = useState("");
  const [userToken, setUserToken] = useState("");
  const [firebaseLoading, setFirebaseLoading] = useState(false);
  const [firebaseError, setFirebaseError] = useState<string | null>(null);

  const { login, loginFirebase, firebaseEnabled } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const goToDestination = () => {
    const redirect = searchParams.get("redirect") ?? "/dashboard";
    router.push(redirect);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const result = await login(credential);
    setLoading(false);
    if (result.error) {
      setError(result.message ?? "Login failed");
    } else {
      goToDestination();
    }
  };

  const handleFirebaseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFirebaseLoading(true);
    setFirebaseError(null);
    const result = await loginFirebase(userId, userToken);
    setFirebaseLoading(false);
    if (result.error) {
      setFirebaseError(result.message ?? "Login failed");
    } else {
      goToDestination();
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-xl border bg-white p-8 shadow-sm">
        <div className="mb-6 flex justify-center">
          <Image
            src="/gustavo_wordmark.png"
            alt="Gustavo"
            width={180}
            height={180}
            priority
          />
        </div>
        <h1 className="mb-1 text-center text-xl font-bold text-gray-900">Sign in to Gustavo</h1>
        <p className="mb-6 text-center text-sm text-gray-500">
          Paste the access credential you were given
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="credential">Access credential</Label>
            <Input
              id="credential"
              type="password"
              value={credential}
              onChange={(e) => setCredential(e.target.value)}
              placeholder="username:token"
              required
              autoComplete="current-password"
              className="mt-1"
            />
            <p className="mt-1 text-xs text-gray-400">
              Format: username:token — the platform admin default is nebula:nebula
            </p>
          </div>
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </Button>
        </form>

        {firebaseEnabled && (
          <div className="mt-6 border-t pt-4">
            <button
              type="button"
              onClick={() => setShowFirebase((v) => !v)}
              className="w-full text-center text-xs font-medium text-gray-400 hover:text-gray-600"
            >
              {showFirebase ? "Hide SSO sign-in" : "Sign in with SSO instead"}
            </button>
            {showFirebase && (
              <form onSubmit={handleFirebaseSubmit} className="mt-4 space-y-4">
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
                {firebaseError && (
                  <Alert variant="destructive">
                    <AlertDescription>{firebaseError}</AlertDescription>
                  </Alert>
                )}
                <Button type="submit" variant="outline" className="w-full" disabled={firebaseLoading}>
                  {firebaseLoading ? "Authenticating…" : "Sign in with SSO"}
                </Button>
              </form>
            )}
          </div>
        )}
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
