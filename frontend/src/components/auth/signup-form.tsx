"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface SignupData {
  full_name: string;
  email: string;
  password: string;
  confirmPassword: string;
  date_of_birth: string;
}

export function SignupForm() {
  const router = useRouter();
  const [formData, setFormData] = useState<SignupData>({
    full_name: "",
    email: "",
    password: "",
    confirmPassword: "",
    date_of_birth: "",
  });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [emailExists, setEmailExists] = useState(false);

  const handleChange = (field: keyof SignupData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const validateForm = (): boolean => {
    if (!formData.full_name || !formData.email || !formData.password || !formData.confirmPassword || !formData.date_of_birth) {
      setError("All fields are required");
      return false;
    }

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters");
      return false;
    }

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          full_name: formData.full_name,
          email: formData.email,
          password: formData.password,
          date_of_birth: formData.date_of_birth,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        
        // Check if email already exists (400 Bad Request with specific message)
        if (res.status === 400 && data.detail === "Email already registered") {
          setEmailExists(true);
          setError("An account with this email already exists.");
          return;
        }
        
        setError(data.detail || "Registration failed. Please try again.");
        return;
      }

      const data = await res.json();
      
      // Registration successful - redirect to login
      router.push("/login?registered=true");
    } catch (err) {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Create Account</CardTitle>
        <CardDescription>
          Start your fitness journey with personalized AI-powered plans
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
              {error}
              {emailExists && (
                <div className="mt-2 pt-2 border-t border-red-300">
                  <a 
                    href="/login" 
                    className="text-blue-600 hover:underline font-medium"
                  >
                    Sign in instead
                  </a>
                  {" or "}
                  <a 
                    href="/forgot-password" 
                    className="text-blue-600 hover:underline font-medium"
                  >
                    reset your password
                  </a>
                </div>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="full_name">Full Name</Label>
            <Input
              id="full_name"
              name="full_name"
              type="text"
              placeholder="Sean Deery"
              value={formData.full_name}
              onChange={handleChange("full_name")}
              required
              disabled={isLoading}
              autoComplete="name"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="sdeery14@gmail.com"
              value={formData.email}
              onChange={handleChange("email")}
              required
              disabled={isLoading}
              autoComplete="email"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange("password")}
              required
              disabled={isLoading}
              autoComplete="new-password"
              minLength={8}
            />
            <p className="text-xs text-gray-500">
              Must be at least 8 characters
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              placeholder="••••••••"
              value={formData.confirmPassword}
              onChange={handleChange("confirmPassword")}
              required
              disabled={isLoading}
              autoComplete="new-password"
              minLength={8}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="date_of_birth">Date of Birth</Label>
            <Input
              id="date_of_birth"
              name="date_of_birth"
              type="date"
              value={formData.date_of_birth}
              onChange={handleChange("date_of_birth")}
              required
              disabled={isLoading}
              max={new Date().toISOString().split('T')[0]}
            />
          </div>
        </CardContent>

        <CardFooter className="flex flex-col space-y-4">
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? "Creating account..." : "Sign Up"}
          </Button>

          <p className="text-sm text-center text-gray-600">
            Already have an account?{" "}
            <a
              href="/login"
              className="font-medium text-primary hover:underline"
            >
              Sign in
            </a>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
